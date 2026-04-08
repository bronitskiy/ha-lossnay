"""Config flow for Mitsubishi Lossnay ERV integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import MelViewAuthError, MelViewClient, MelViewError
from .const import CONF_UNIT_ID, CONF_UNIT_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


async def _discover_units(
    hass: HomeAssistant, email: str, password: str
) -> list[dict[str, Any]]:
    """Login and return list of ERV units."""
    session = async_get_clientsession(hass)
    client = MelViewClient(session, email, password)
    await client.login()
    return await client.get_erv_units()


class LossnayConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow for Lossnay."""

    VERSION = 1

    def __init__(self) -> None:
        self._email: str = ""
        self._password: str = ""
        self._units: list[dict[str, Any]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle the initial credential step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._email = user_input[CONF_EMAIL]
            self._password = user_input[CONF_PASSWORD]

            try:
                self._units = await _discover_units(
                    self.hass, self._email, self._password
                )
            except MelViewAuthError:
                errors["base"] = "invalid_auth"
            except MelViewError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error during unit discovery")
                errors["base"] = "unknown"

            if not errors:
                if not self._units:
                    errors["base"] = "no_units_found"
                elif len(self._units) == 1:
                    return await self._create_entry(self._units[0])
                else:
                    return await self.async_step_select_unit()

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
        )

    async def async_step_select_unit(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle unit selection when multiple ERV units are found."""
        if user_input is not None:
            selected_id = user_input[CONF_UNIT_ID]
            unit = next(u for u in self._units if u["unitid"] == selected_id)
            return await self._create_entry(unit)

        unit_options = {u["unitid"]: u["name"] for u in self._units}

        return self.async_show_form(
            step_id="select_unit",
            data_schema=vol.Schema(
                {vol.Required(CONF_UNIT_ID): vol.In(unit_options)}
            ),
        )

    async def _create_entry(self, unit: dict[str, Any]) -> config_entries.FlowResult:
        """Create the config entry."""
        await self.async_set_unique_id(unit["unitid"])
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=unit["name"],
            data={
                CONF_EMAIL: self._email,
                CONF_PASSWORD: self._password,
                CONF_UNIT_ID: unit["unitid"],
                CONF_UNIT_NAME: unit["name"],
            },
        )
