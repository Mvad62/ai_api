import asyncio
import logging

from aiogram import Bot, Dispatcher, Router
from aiogram.exceptions import TelegramRetryAfter, TelegramUnauthorizedError
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from api_client import APIClientError, AnyModelClient
from config import load_config
from context_manager import ContextManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

MAX_MESSAGE_LENGTH = 4000
SEND_MAX_ATTEMPTS = 4

config = load_config()
bot = Bot(token=config.bot_token)
dispatcher = Dispatcher()
router = Router()
contexts = ContextManager(max_messages=config.max_history_messages)
api_client = AnyModelClient(config.anymodel_key, config.api_base_url)


async def safe_answer(message: Message, text: str) -> None:
    """Send a reply, respecting Telegram flood control (TelegramRetryAfter)."""
    for attempt in range(1, SEND_MAX_ATTEMPTS + 1):
        try:
            await message.answer(text)
            return
        except TelegramRetryAfter as exc:
            if attempt == SEND_MAX_ATTEMPTS:
                logger.error(
                    "Giving up sending reply after %d attempts due to flood control",
                    attempt,
                )
                return
            logger.warning(
                "Flood control while sending reply (attempt %d/%d); retrying in %s seconds",
                attempt,
                SEND_MAX_ATTEMPTS,
                exc.retry_after,
            )
            await asyncio.sleep(exc.retry_after)


@router.message(CommandStart())
async def start(message: Message) -> None:
    await safe_answer(
        message,
        "Привет! Напиши сообщение, чтобы начать диалог. "
        "Команда /reset очистит историю.",
    )


@router.message(Command("reset"))
async def reset_context(message: Message) -> None:
    if message.from_user is not None:
        user_id = message.from_user.id
        async with contexts.lock_for(user_id):
            contexts.clear(user_id)
    await safe_answer(message, "Контекст очищен.")


@router.message()
async def chat(message: Message) -> None:
    if message.from_user is None or not message.text:
        await safe_answer(message, "Пожалуйста, отправь текстовое сообщение.")
        return

    user_id = message.from_user.id
    async with contexts.lock_for(user_id):
        messages = contexts.get_messages(user_id)
        messages.append({"role": "user", "content": message.text})
        try:
            answer, _usage = await api_client.complete(
                model=config.model,
                messages=messages,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
            )
        except APIClientError:
            logger.exception("Failed to answer Telegram user %s", user_id)
            await safe_answer(message, "Не удалось получить ответ от модели. Попробуй позже.")
            return

        contexts.add_message(user_id, "user", message.text)
        contexts.add_message(user_id, "assistant", answer)
        for offset in range(0, len(answer), MAX_MESSAGE_LENGTH):
            await safe_answer(message, answer[offset : offset + MAX_MESSAGE_LENGTH])


async def wait_for_bot_info(bot: Bot, max_attempts: int = 4) -> None:
    for attempt in range(1, max_attempts + 1):
        try:
            await bot.me()
            return
        except TelegramUnauthorizedError:
            logger.error("BOT_TOKEN is invalid or was revoked; update .env and run again")
            raise SystemExit(1) from None
        except TelegramRetryAfter as exc:
            if attempt == max_attempts:
                logger.error(
                    "Telegram keeps rate-limiting this bot token: %d attempts, last "
                    "retry_after=%s seconds. Make sure no other instance, deployment "
                    "or third-party service uses the same token; revoke it in BotFather "
                    "and put the new one into .env, then run again",
                    attempt,
                    exc.retry_after,
                )
                raise SystemExit(1) from None
            delay = exc.retry_after * attempt
            logger.warning(
                "Telegram rate limit while checking bot info (attempt %d/%d); "
                "retrying in %s seconds",
                attempt,
                max_attempts,
                delay,
            )
            await asyncio.sleep(delay)


async def main() -> None:
    dispatcher.include_router(router)
    try:
        await wait_for_bot_info(bot)
        await dispatcher.start_polling(bot, close_bot_session=False)
    finally:
        await api_client.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
