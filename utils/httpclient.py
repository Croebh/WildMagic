import abc
import logging

import aiohttp

from errors import WildException


class HTTPException(WildException):
    pass


class HTTPTimeout(HTTPException):
    pass


class HTTPStatusException(HTTPException):
    def __init__(self, status_code: int, msg: str):
        super().__init__(msg)
        self.status_code = status_code


class BaseClient(abc.ABC):
    SERVICE_BASE: str = ...
    logger: logging.Logger = logging.getLogger(__name__)

    def __init__(self, http: aiohttp.ClientSession):
        self.http = http

    async def request(self, method: str, route: str, response_as_text=False, **kwargs):
        service_base = kwargs.get("service_base", self.SERVICE_BASE)
        if "service_base" in kwargs:
            kwargs.pop("service_base")

        try:
            async with self.http.request(
                method, f"{service_base}{route}", **kwargs
            ) as resp:
                self.logger.debug(
                    f"{method} {service_base}{route} returned {resp.status}"
                )
                if not 199 < resp.status < 300:
                    data = await resp.text()
                    self.logger.warning(
                        f"{method} {service_base}{route} returned {resp.status} {resp.reason}\n{data}"
                    )
                    raise HTTPStatusException(
                        resp.status,
                        f"Request returned an error: {resp.status}: {resp.reason}",
                    )
                try:
                    if not response_as_text:
                        data = await resp.json()
                    else:
                        data = await resp.text()
                    self.logger.debug(data)
                except (aiohttp.ContentTypeError, ValueError, TypeError):
                    data = await resp.text()
                    self.logger.warning(
                        f"{method} {service_base}{route} response could not be deserialized:\n{data}"
                    )
                    raise HTTPException(f"Could not deserialize response: {data}")
        except aiohttp.ServerTimeoutError:
            self.logger.warning(f"Request timeout: {method} {service_base}{route}")
            raise HTTPTimeout(
                "Timed out connecting. Please try again in a few minutes."
            )
        return data

    async def get(self, route: str, **kwargs):
        return await self.request("GET", route, **kwargs)

    async def post(self, route: str, **kwargs):
        return await self.request("POST", route, **kwargs)

    async def close(self):
        await self.http.close()
