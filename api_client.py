import logging

import httpx

logger = logging.getLogger(__name__)


class APIClientError(RuntimeError):
    pass


class AnyModelClient:
    def __init__(self, api_key: str, base_url: str, timeout: float = 60.0) -> None:
        self._api_key = api_key
        self._url = f"{base_url}/chat/completions"
        self._client = httpx.AsyncClient(timeout=timeout)

    async def close(self) -> None:
        await self._client.aclose()

    async def complete(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> tuple[str, dict]:
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        logger.info(
            "Sending chat completion parameters: model=%s temperature=%s "
            "max_tokens=%s message_count=%d message_roles=%s",
            model,
            temperature,
            max_tokens,
            len(messages),
            [message["role"] for message in messages],
        )
        try:
            response = await self._client.post(
                self._url,
                headers={"Authorization": f"Bearer {self._api_key}"},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            answer = data["choices"][0]["message"]["content"]
            if not isinstance(answer, str) or not answer:
                raise ValueError("API returned an empty or invalid assistant response")
            usage = data.get("usage", {})
            logger.info(
                "Chat completion succeeded: request_id=%s usage=%s",
                response.headers.get("x-request-id"),
                usage,
            )
            return answer, usage
        except httpx.HTTPStatusError as exc:
            logger.error(
                "API returned HTTP %s: %s",
                exc.response.status_code,
                exc.response.text[:1000],
            )
            raise APIClientError(f"API returned HTTP {exc.response.status_code}") from exc
        except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError) as exc:
            logger.exception("Chat completion request failed")
            raise APIClientError("Could not get a valid response from the API") from exc
