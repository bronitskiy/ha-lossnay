"""Async MelView API client for Mitsubishi Lossnay ERV."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp

from .const import (
    APP_VERSION,
    ERV_TYPE,
    MELVIEW_LOGIN_URL,
    MELVIEW_ROOMS_URL,
    MELVIEW_UNIT_COMMAND_URL,
)

_LOGGER = logging.getLogger(__name__)

HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "User-Agent": "Mozilla/5.0 (compatible; ha-lossnay/1.0)",
}


class MelViewAuthError(Exception):
    """Raised when authentication fails."""


class MelViewError(Exception):
    """Raised on general API errors."""


class MelViewClient:
    """Async client for the MelView cloud API."""

    def __init__(self, session: aiohttp.ClientSession, email: str, password: str) -> None:
        self._session = session
        self._email = email
        self._password = password
        self._cookie_jar = aiohttp.CookieJar()

    async def login(self) -> None:
        """Authenticate and store session cookies.

        MelView expects a JSON body but with the application/x-www-form-urlencoded
        Content-Type header — this matches the behaviour of the official app.
        """
        import json as _json

        body = _json.dumps(
            {"user": self._email, "pass": self._password, "appversion": APP_VERSION}
        ).encode()
        try:
            async with self._session.post(
                MELVIEW_LOGIN_URL,
                data=body,
                headers=HEADERS,
            ) as resp:
                if resp.status in (401, 403):
                    raise MelViewAuthError(f"Login failed with HTTP {resp.status}")
                if resp.status != 200:
                    raise MelViewAuthError(f"Login failed with HTTP {resp.status}")
                _LOGGER.debug("MelView login successful")
        except aiohttp.ClientError as err:
            raise MelViewError(f"Network error during login: {err}") from err

    async def get_erv_units(self) -> list[dict[str, Any]]:
        """Return a list of ERV units from rooms.aspx."""
        data = await self._post(MELVIEW_ROOMS_URL, {})
        units: list[dict[str, Any]] = []
        if not isinstance(data, list):
            _LOGGER.warning("Unexpected rooms response: %s", data)
            return units
        for room in data:
            for unit in room.get("units", []):
                if unit.get("type", "").upper() == ERV_TYPE:
                    units.append(
                        {
                            "unitid": str(unit.get("unitid", "")),
                            "name": unit.get("room", unit.get("name", "Lossnay")),
                        }
                    )
        return units

    async def get_unit_state(self, unit_id: str) -> dict[str, Any]:
        """Fetch the current state of a unit."""
        return await self._post(
            MELVIEW_UNIT_COMMAND_URL,
            {"unitid": unit_id, "v": 2, "commands": ""},
        )

    async def send_command(self, unit_id: str, command: str) -> dict[str, Any]:
        """Send a command string to a unit (e.g. 'PW1', 'FS2', 'MD3')."""
        _LOGGER.debug("Sending command %s to unit %s", command, unit_id)
        return await self._post(
            MELVIEW_UNIT_COMMAND_URL,
            {"unitid": unit_id, "v": 2, "commands": command},
        )

    async def _post(self, url: str, payload: dict[str, Any]) -> Any:
        """POST JSON payload, re-authenticate on 401/403."""
        import json as _json

        body = _json.dumps(payload)
        try:
            async with self._session.post(
                url,
                data=body,
                headers={**HEADERS, "Content-Type": "application/json; charset=UTF-8"},
            ) as resp:
                if resp.status in (401, 403):
                    _LOGGER.debug("Session expired, re-authenticating")
                    await self.login()
                    # Retry once after re-auth
                    async with self._session.post(
                        url,
                        data=body,
                        headers={
                            **HEADERS,
                            "Content-Type": "application/json; charset=UTF-8",
                        },
                    ) as retry_resp:
                        retry_resp.raise_for_status()
                        return await retry_resp.json(content_type=None)

                resp.raise_for_status()
                return await resp.json(content_type=None)
        except aiohttp.ClientResponseError as err:
            raise MelViewError(f"API request to {url} failed: {err}") from err
        except aiohttp.ClientError as err:
            raise MelViewError(f"Network error reaching {url}: {err}") from err
