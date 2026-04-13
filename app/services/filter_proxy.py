"""
filter_proxy.py
───────────────
Proxies the resolved filter payload to the Java Spring Boot backend.
Returns the raw response as-is so Angular can render it with the
existing table component.
"""

import logging
import httpx
from config import settings

logger = logging.getLogger(__name__)

TIMEOUT = 30.0


class FilterProxy:

    def __init__(self):
        self._base_url = settings.java_backend_url
        self._endpoint = settings.java_filter_endpoint

    async def execute(self, payload: dict) -> dict:
        """
        POST the filter payload to the Java backend.
        Returns the raw JSON response from Java.
        Raises httpx.HTTPError on failure.
        """
        url = f"{self._base_url}{self._endpoint}"
        logger.info("Proxying filter request to: %s", url)
        logger.debug("Payload: %s", payload)

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            data = response.json()

        logger.info("Java backend returned %d items", self._count_items(data))
        return data

    def _count_items(self, data: dict) -> int:
        """Try to extract item count from response for logging."""
        if isinstance(data, list):
            return len(data)
        for key in ("content", "items", "data", "results"):
            if key in data and isinstance(data[key], list):
                return len(data[key])
        return -1
