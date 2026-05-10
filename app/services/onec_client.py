import httpx

from app.config import settings
from app.core.errors import TargetOneCError


TARGET_URLS = {
    "unf": settings.ONEC_UNF_URL,
    "bp": settings.ONEC_BP_URL,
}


def get_target_url(target: str) -> str:
    try:
        return TARGET_URLS[target]
    except KeyError:
        raise ValueError(f"Unknown target: {target}")


def get_onec_auth() -> httpx.BasicAuth | None:
    if settings.ONEC_LOGIN and settings.ONEC_PASSWORD:
        return httpx.BasicAuth(
            settings.ONEC_LOGIN,
            settings.ONEC_PASSWORD,
        )

    return None


async def send_to_1c(
    target: str,
    entity: str,
    file_content: bytes,
    filename: str,
) -> dict:
    url = get_target_url(target)
    auth = get_onec_auth()

    print("1C URL:", url)
    print("1C login:", settings.ONEC_LOGIN)
    print("1C password exists:", bool(settings.ONEC_PASSWORD))
    print("1C auth enabled:", bool(auth))
    print("1C entity:", entity)
    print("1C filename:", filename)
    print("FILE CONTENT TO 1C:")
    print(file_content.decode("utf-8-sig", errors="replace"))
    

    try:
        async with httpx.AsyncClient(
        timeout=settings.ONEC_TIMEOUT,
        trust_env=False,
        ) as client:
            response = await client.post(
                url,
                auth=auth,
                headers={
                    "Content-Type": "text/csv; charset=utf-8",
                    "X-Entity": entity,
                    "X-File-Type": entity,
                    "File-Type": entity,
                    "X-Filename": filename,
                },
                content=file_content,
        )

        print("1C requested URL:", response.request.url)
        print("1C response status:", response.status_code)
        print("1C response text:", response.text)

    except httpx.TimeoutException:
        raise TargetOneCError(
            message=f"Timeout while sending data to target 1C. URL: {url}",
        )

    except httpx.RequestError as exc:
        raise TargetOneCError(
            message=f"Could not connect to target 1C. URL: {url}. Error: {str(exc)}",
        )

    if response.status_code >= 400:
        raise TargetOneCError(
            message=f"Target 1C returned error. URL: {url}",
            status_code=response.status_code,
            response_text=response.text,
        )

    try:
        response_json = response.json()
    except ValueError:
        response_json = None

    return {
        "status_code": response.status_code,
        "json": response_json,
        "text": response.text,
    }