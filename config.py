import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    bot_token: str
    anymodel_key: str
    api_base_url: str
    model: str
    temperature: float
    max_tokens: int
    max_history_messages: int


def load_config() -> Config:
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    anymodel_key = os.getenv("ANYMODEL_KEY", "").strip()
    model = os.getenv("ANYMODEL_MODEL", "").strip()
    if not bot_token:
        raise ValueError("BOT_TOKEN is required")
    if not anymodel_key:
        raise ValueError("ANYMODEL_KEY is required")
    if not model:
        raise ValueError("ANYMODEL_MODEL is required")

    try:
        temperature = float(os.getenv("TEMPERATURE", "0.7"))
        max_tokens = int(os.getenv("MAX_TOKENS", "1000"))
        max_history_messages = int(os.getenv("MAX_HISTORY_MESSAGES", "20"))
    except ValueError as exc:
        raise ValueError(
            "TEMPERATURE, MAX_TOKENS and MAX_HISTORY_MESSAGES must be numeric"
        ) from exc
    if not 0 <= temperature <= 2:
        raise ValueError("TEMPERATURE must be between 0 and 2")
    if max_tokens <= 0 or max_history_messages <= 0:
        raise ValueError("MAX_TOKENS and MAX_HISTORY_MESSAGES must be positive")

    return Config(
        bot_token=bot_token,
        anymodel_key=anymodel_key,
        api_base_url=os.getenv("ANYMODEL_BASE_URL", "https://anymodel.org/v1").rstrip("/"),
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        max_history_messages=max_history_messages,
    )
