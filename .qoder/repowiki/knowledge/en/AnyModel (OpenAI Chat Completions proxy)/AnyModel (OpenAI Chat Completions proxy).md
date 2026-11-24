---
kind: external_dependency
name: AnyModel (OpenAI Chat Completions proxy)
slug: anymodel
category: external_dependency
category_hints:
    - vendor_identity
    - sdk_real_api
scope:
    - '**'
source_files:
    - api_client.py
    - config.py
    - bot.py
---

### AnyModel
- Role: OpenAI Chat Completions–compatible LLM proxy used as the model backend instead of calling OpenAI directly.
- The README states the default model is `gpt-6.1-sol` with `temperature=0.7`, `max_tokens=1000`, and 20-message history when no overrides are set.
- Verify exact request/response shape against AnyModel's OpenAI-compatible API docs.