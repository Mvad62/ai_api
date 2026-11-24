---
kind: external_dependency
name: Telegram Bot API (aiogram)
slug: telegram-bot-api
category: external_dependency
category_hints:
    - client_constraint
    - framework_behavior
scope:
    - '**'
source_files:
    - bot.py
---

### Telegram Bot API
- Integration point: `aiogram>=3.7,<4.0` (`Bot`, `Dispatcher`, `Router`, `Message`, `CommandStart`, `TelegramRetryAfter`).
- Constraint: rapid restarts or multiple processes sharing one token trigger flood-control 429 on `getMe`. A 429 raised *during* polling (`getUpdates`/`sendMessage`) is not retried — aiogram raises it and the process exits with a traceback.
- Verify exact method/params against the official Telegram Bot API docs.