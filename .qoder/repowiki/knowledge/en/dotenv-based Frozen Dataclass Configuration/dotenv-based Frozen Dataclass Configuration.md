---
kind: configuration_system
name: dotenv-based Frozen Dataclass Configuration
category: configuration_system
scope:
    - '**'
source_files:
    - config.py
    - .env.example
    - bot.py
---

## Approach

Configuration is loaded from environment variables via `python-dotenv` (`load_dotenv()`), with a `.env.example` template documenting the expected keys. Values are parsed and validated into an immutable `dataclasses.dataclass(frozen=True)` named `Config`, then consumed as a single module-level singleton in `bot.py`.

## Key Files

- `config.py` — configuration loader and schema definition
- `.env.example` — template of all supported environment variables
- `bot.py` — consumes the `Config` instance at import time

## Architecture

1. **Load order**: `config.py` calls `load_dotenv()` at import time, which reads `.env` (if present) into `os.environ`. Then `bot.py` imports `config` and immediately calls `load_config()`, so all config resolution happens before any Telegram or API client is instantiated.
2. **Schema**: `Config` is a frozen dataclass with seven fields: `bot_token`, `anymodel_key`, `api_base_url`, `model`, `temperature`, `max_tokens`, `max_history_messages`. Freezing makes it effectively immutable after construction.
3. **Loading function**: `load_config()` reads each value via `os.getenv(name, default)`, strips whitespace on required string fields, casts optional numeric/float fields, and validates them before returning the `Config` instance.
4. **Consumption**: `bot.py` holds a module-level `config = load_config()` and passes individual fields to `Bot(token=...)`, `AnyModelClient(...)`, and `ContextManager(max_messages=...)`.

## Environment Variables

| Variable | Required? | Default | Validation / Notes |
|---|---:|---|---|
| `BOT_TOKEN` | Yes | — | Stripped; raises `ValueError("BOT_TOKEN is required")` if empty |
| `ANYMODEL_KEY` | Yes | — | Stripped; raises `ValueError("ANYMODEL_KEY is required")` if empty |
| `TEMPERATURE` | No | `0.7` | Cast to float; must be in `[0, 2]` |
| `MAX_TOKENS` | No | `1000` | Cast to int; must be positive |
| `MAX_HISTORY_MESSAGES` | No | `20` | Cast to int; must be positive |
| `ANYMODEL_BASE_URL` | No | `https://api.openai.com/v1` | Trailing slash stripped via `.rstrip("/")` |
| `ANYMODEL_MODEL` | No | `gpt-4o-mini` | Passed through as-is |

## Conventions & Constraints

- All runtime configuration comes from environment variables; no YAML/TOML/JSON config files are used.
- Secrets (`BOT_TOKEN`, `ANYMODEL_KEY`) are never hard-coded — they are read from `os.environ` and raise `ValueError` when missing.
- Optional settings use explicit defaults inside `os.getenv(..., default)` rather than relying on `None` coalescing.
- Numeric parameters are validated at load time (not lazily), failing fast during process startup:
  - `TEMPERATURE` must satisfy `0 <= temperature <= 2` (`config.py:31`).
  - `MAX_TOKENS` and `MAX_HISTORY_MESSAGES` must be positive integers (`config.py:33`).
- The `Config` object is frozen (`frozen=True`), preventing mutation after creation.
- There is no configuration layering or precedence system beyond dotenv + OS env; `.env` is merged by `python-dotenv` into `os.environ`, so OS env vars take final precedence.
- There is no hot-reloading or reload-on-change mechanism; configuration is resolved once at import time.