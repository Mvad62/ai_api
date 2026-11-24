---
kind: logging_system
name: Standard Library logging with basicConfig and per-module loggers
category: logging_system
scope:
    - '**'
source_files:
    - bot.py
    - api_client.py
---

## What system/approach is used

The project uses Python's standard library `logging` module exclusively — no third-party logging framework (e.g. structlog, loguru, python-json-logger) is imported or configured.

## Key files and packages

- `bot.py` — entry point that configures the root logger via `logging.basicConfig` and defines a module-level `logger = logging.getLogger(__name__)`.
- `api_client.py` — creates its own module-level logger (`logger = logging.getLogger(__name__)`) and emits INFO/ERROR/EXCEPTION logs around HTTP calls to the OpenAI-compatible API.
- Other modules (`config.py`, `context_manager.py`, `prompt.txt`, `.env.example`) do not import or use `logging`.

## Architecture and conventions

1. **Single global configuration.** `bot.py` calls `logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")` at module load time. This sets the root logger level to `INFO` and applies a fixed human-readable format (timestamp, level, module name, message) to all handlers.
2. **Per-module logger instances.** Each file that needs logging imports `logging` and obtains a logger via `logging.getLogger(__name__)`. There is no shared logger factory or custom Logger subclass.
3. **Log levels observed:**
   - `INFO`: request parameters sent to the API and successful completion (including `x-request-id` header and usage metadata).
   - `WARNING`: Telegram rate-limit backoff in `wait_for_bot_info`.
   - `ERROR`: HTTP status errors from the API client, including truncated response text.
   - `EXCEPTION`: raised via `logger.exception(...)` for unexpected failures (in both `bot.py`'s chat handler and `api_client.py`'s broad exception branch), which automatically appends the traceback.
4. **No structured output.** Log messages are plain strings with positional `%s` formatting; there is no JSON serialization, no dedicated fields object, and no correlation ID propagated across modules beyond what happens to be embedded in the message string.
5. **No custom sinks or rotation.** The default `basicConfig` call does not attach any FileHandler or StreamHandler explicitly, so output goes to stderr via the default StreamHandler. No rotating file handler, log aggregation, or environment-driven sink selection is present.
6. **No log-level configuration via environment/config.** The level is hard-coded as `logging.INFO` in `bot.py`; `config.py` does not expose a logging-related setting.

## Conventions and constraints

- Every logging site uses `logger = logging.getLogger(__name__)` rather than calling `logging.info/error` directly on the module — this gives each module its own logger name (observed in both `bot.py` and `api_client.py`).
- Exceptions are logged with `logger.exception(...)` when they are re-raised as `APIClientError`, ensuring tracebacks are included alongside the contextual message.
- Sensitive data is not logged: the API key is never interpolated into log messages; only model name, temperature, max_tokens, message count, roles, and the `x-request-id` header are emitted.
- The log format is fixed by `basicConfig` and cannot be overridden at runtime through configuration.