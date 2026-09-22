import requests
from django.conf import settings
from loguru import logger


def fetch_mappedin_token():
    url = "https://app.mappedin.com/api/v1/api-key/token"

    logger.debug(
        f"Mappedin Key: {settings.MAPPEDIN_KEY}, Mappedin Secret: {settings.MAPPEDIN_SECRET}"
    )

    payload = {"key": settings.MAPPEDIN_KEY, "secret": settings.MAPPEDIN_SECRET}

    # Hit Mappedin's authentication endpoint
    response = requests.post(url, json=payload, timeout=10)

    if not response.ok:
        logger.error(f"[Mappedin Error] Status {response.status_code}: {response.text}")

    response.raise_for_status()

    data = response.json()

    return {"token": data.get("access_token"), "expires_in": data.get("expires_in")}
