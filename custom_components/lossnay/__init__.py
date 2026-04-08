"""Mitsubishi Lossnay ERV integration for Home Assistant."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import MelViewClient, MelViewError
from .const import CONF_UNIT_ID, DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.CLIMATE, Platform.FAN, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Lossnay from a config entry."""
    session = async_get_clientsession(hass)
    client = MelViewClient(
        session,
        entry.data[CONF_EMAIL],
        entry.data[CONF_PASSWORD],
    )

    # Login on startup
    await client.login()

    unit_id = entry.data[CONF_UNIT_ID]

    coordinator = LossnayCoordinator(hass, client, unit_id)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator,
        "client": client,
        "unit_id": unit_id,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


class LossnayCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator that polls the Lossnay unit every SCAN_INTERVAL."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: MelViewClient,
        unit_id: str,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"Lossnay {unit_id}",
            update_interval=SCAN_INTERVAL,
        )
        self.client = client
        self.unit_id = unit_id

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch the latest unit state."""
        try:
            data = await self.client.get_unit_state(self.unit_id)
        except MelViewError as err:
            raise UpdateFailed(f"Error communicating with MelView API: {err}") from err
        _LOGGER.debug("Lossnay state: %s", data)
        return data
