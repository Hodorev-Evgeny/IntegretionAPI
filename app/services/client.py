import httpx

from app.config import settings
from app.core.errors import TargetOneCError


TARGET_URLS = {
    "unf": settings.ONEC_UNF_URL,
    "bp": settings.ONEC_BP_URL,
}


def get_target_url(target: str, entity: str) -> str:
    try:
        return TARGET_URLS[target][entity]
    except KeyError:
        raise ValueError(f"Unknown target/entity combination: {target}/{entity}")


async def send_to_1c(
    target: str,
    entity: str,
    payload: dict,
) -> dict:
    url = get_target_url(target, entity)

    try:
        async with httpx.AsyncClient(timeout=settings.ONEC_TIMEOUT) as client:
            response = await client.post(url, json=payload)

    except httpx.TimeoutException:
        raise TargetOneCError(
            message="Timeout while sending data to target 1C",
        )

    except httpx.RequestError as exc:
        raise TargetOneCError(
            message=f"Could not connect to target 1C: {str(exc)}",
        )

    if response.status_code >= 400:
        raise TargetOneCError(
            message="Target 1C returned error",
            status_code=response.status_code,
            response_text=response.text,
        )

    try:
        return {
            "status_code": response.status_code,
            "json": response.json(),
            "text": response.text,
        }
    except ValueError:
        return {
            "status_code": response.status_code,
            "json": None,
            "text": response.text,
        }