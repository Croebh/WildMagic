import aiohttp

from utils.httpclient import BaseClient, HTTPStatusException


class DDBClient(BaseClient):
    SERVICE_BASE = "https://character-service.dndbeyond.com/character/v5/character/"

    def __init__(self, http: aiohttp.ClientSession, api_key: str):
        super().__init__(http)
        self.api_key = api_key

    async def request(self, method: str, route: str, headers=None, **kwargs):
        if headers is None:
            headers = {}
        headers["Authorization"] = self.api_key
        if kwargs.get("noauth"):
            headers.pop("Authorization")
            kwargs.pop("noauth")
        return await super().request(method, route, headers=headers, **kwargs)

    async def get_character(self, char_id: str):
        try:
            char = await self.get(char_id)
            char = char["data"]
        except HTTPStatusException as e:
            self.logger.debug(e)
            error_message = "Unknown error occurred. Please try again later."
            if e.status_code == 404:
                error_message = (
                    "Character was not found. Potentially deactivated, or deleted."
                )
            elif e.status_code == 403:
                error_message = "Character is unavailable. Potentially due to being marked as private."
            return None, error_message

        try:
            avr_api = await self.get(
                char_id,
                service_base="https://character-service-scds.dndbeyond.com/v1/avrae/",
                noauth=True,
            )
            char["avrae"] = avr_api
        except HTTPStatusException as e:
            self.logger.debug(e)
            error_message = "Unknown error occurred. Please try again later."
            if e.status_code == 404:
                error_message = (
                    "Character was not found. Potentially deactivated, or deleted."
                )
            elif e.status_code == 403:
                error_message = "Character is unavailable. Potentially due to being marked as private."
            return None, error_message

        return char, None
