---
kind: business_term
name: Business Glossary
category: business_term
scope:
    - '**'
---

### контекст
- Definition：Per-user conversation history maintained in-process by `ContextManager`; stored as a list of `{role, content}` message dicts and truncated to the last `MAX_HISTORY_MESSAGES` entries. Cleared via the `/reset` command; does not survive bot restarts.
- Aliases：context、history
