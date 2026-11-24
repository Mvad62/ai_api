---
kind: error_handling
name: Error Handling in Telegram Chatbot (APIClientError, Logging, Retry-After)
category: error_handling
scope:
    - '**'
source_files:
    - api_client.py
    - bot.py
    - config.py
---

## Overview

This is a small aiogram 3 + httpx Python project. Error handling is minimal and localized to two layers:

1. **Configuration validation** raises `ValueError` at startup.
2. **HTTP/API layer** wraps all failures in a single sentinel exception `APIClientError`, logs the underlying cause, and propagates it upward.
3. **Bot handlers** catch `APIClientError` to present a user-friendly Russian message and log the failure with full traceback.
4. **Telegram rate-limiting** is handled by catching `aiogram.exceptions.TelegramRetryAfter` and sleeping for the reported delay.

There is no middleware, no global error handler, no structured error hierarchy beyond the single custom exception, and no `try/except` around the in-memory `ContextManager`.

## Key Files

- `api_client.py` — defines `APIClientError(RuntimeError)` and the only place where external I/O errors are converted into application errors.
- `bot.py` — catches `APIClientError` in the chat handler; catches `TelegramRetryAfter` in `wait_for_bot_info`; sets up root logging via `logging.basicConfig`.
- `config.py` — validates environment variables and raises `ValueError` when required keys or ranges are missing.
- `context_manager.py` — no error handling; relies on caller-managed locks.

## Architecture & Conventions

### Custom sentinel error

```python
class APIClientError(RuntimeError):
    pass
```

`AnyModelClient.complete()` is the sole producer of this exception. All HTTP and parsing failures funnel through one block:

- `httpx.HTTPStatusError` → logs status code + first 1000 chars of response body → raises `APIClientError(f"API returned HTTP {exc.response.status_code}") from exc`.
- Any other `httpx.HTTPError`, `ValueError`, `KeyError`, `IndexError`, or `TypeError` → logs via `logger.exception("Chat completion request failed")` → raises `APIClientError("Could not get a valid response from the API") from exc`.

The use of `raise ... from exc` preserves the original traceback chain.

### Handler-level swallowing

In `bot.py`'s `chat` handler:

```python
try:
    answer, _usage = await api_client.complete(...)
except APIClientError:
    logger.exception("Failed to answer Telegram user %s", user_id)
    await message.answer("Не удалось получить ответ от модели. Попробуй позже.")
    return
```

Errors are caught per-message, logged with the user ID, translated into a user-facing Russian message, and then swallowed (the handler returns without re-raising). This prevents a failing LLM call from crashing the polling loop.

### Telegram rate limiting

`wait_for_bot_info` explicitly catches `aiogram.exceptions.TelegramRetryAfter`:

```python
except TelegramRetryAfter as exc:
    logger.warning(
        "Telegram rate limit while checking bot info; retrying in %s seconds",
        exc.retry_after,
    )
    await asyncio.sleep(exc.retry_after)
```

It retries indefinitely until the bot's own metadata can be fetched.

### Startup / config errors

`config.load_config()` raises `ValueError` for:
- Missing `BOT_TOKEN`
- Missing `ANYMODEL_KEY`
- Temperature outside `[0, 2]`
- Non-positive `MAX_TOKENS` / `MAX_HISTORY_MESSAGES`

These are not caught anywhere in `bot.py`; they propagate out of `main()` and terminate the process, which is appropriate for configuration-time failures.

### Logging

Logging is configured once at module load:

```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
```

All error paths use `logger.error` or `logger.exception`. There is no separate error/warn/info file routing.

### What is NOT done

- No global aiogram error handler (`dispatcher.error_handler`) is registered.
- No `try/finally` around individual message handlers (only the top-level `main()` has a `finally` that closes `api_client` and `bot.session`).
- `ContextManager` does not raise or catch anything; concurrency is managed by an explicit per-user `asyncio.Lock` exposed via `lock_for`.
- No structured error codes, error-response objects, or telemetry integration.

## Conventions Observed

1. External I/O failures are wrapped in the single `APIClientError(RuntimeError)` sentinel rather than propagated as raw `httpx` exceptions.
2. Every `raise APIClientError` uses `from exc` to preserve the original exception chain.
3. The bot handler catches `APIClientError` and responds to the user with a fixed Russian fallback message instead of exposing internal details.
4. Telegram-specific `TelegramRetryAfter` is caught separately from generic API errors, since it represents a transient rate-limit condition rather than a client failure.
5. Configuration validation fails fast with `ValueError` at import/startup time.
6. Resource cleanup (`api_client.close()`, `bot.session.close()`) is placed in a `finally` block in `main()`.