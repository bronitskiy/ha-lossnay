"""Fan entity for Mitsubishi Lossnay ERV."""
from __future__ import annotations

import logging
import math
from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import LossnayCoordinator
from .api import MelViewClient, MelViewError
from .const import (
    CMD_POWER_OFF,
    CMD_POWER_ON,
    CONF_UNIT_ID,
    CONF_UNIT_NAME,
    DOMAIN,
    FAN_PRESET_TO_CMD,
    FAN_PRESETS,
    FAN_SPEED_MAP,
    PERCENTAGE_TO_FAN_CMD,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Lossnay fan entity."""
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            LossnayFan(
                coordinator=data["coordinator"],
                client=data["client"],
                unit_id=data["unit_id"],
                unit_name=entry.data[CONF_UNIT_NAME],
                entry_id=entry.entry_id,
            )
        ]
    )


class LossnayFan(CoordinatorEntity[LossnayCoordinator], FanEntity):
    """Representation of the Lossnay fan."""

    _attr_has_entity_name = True
    _attr_name = None  # use device name as entity name
    _attr_supported_features = (
        FanEntityFeature.SET_SPEED
        | FanEntityFeature.PRESET_MODE
        | FanEntityFeature.TURN_ON
        | FanEntityFeature.TURN_OFF
    )
    _attr_preset_modes = FAN_PRESETS

    def __init__(
        self,
        coordinator: LossnayCoordinator,
        client: MelViewClient,
        unit_id: str,
        unit_name: str,
        entry_id: str,
    ) -> None:
        super().__init__(coordinator)
        self._client = client
        self._unit_id = unit_id
        self._unit_name = unit_name
        self._attr_unique_id = f"{entry_id}_fan"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, unit_id)},
            "name": unit_name,
            "manufacturer": "Mitsubishi Electric",
            "model": "Lossnay ERV",
        }

    @property
    def is_on(self) -> bool:
        """Return True if the fan is on."""
        return bool(self.coordinator.data.get("power", 0))

    @property
    def percentage(self) -> int | None:
        """Return the current fan speed as a percentage."""
        speed_cmd = self.coordinator.data.get("setfan")
        if speed_cmd is None:
            return None
        info = FAN_SPEED_MAP.get(int(speed_cmd))
        return info[1] if info else None

    @property
    def preset_mode(self) -> str | None:
        """Return the current preset mode."""
        speed_cmd = self.coordinator.data.get("setfan")
        if speed_cmd is None:
            return None
        info = FAN_SPEED_MAP.get(int(speed_cmd))
        return info[0] if info else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        data = self.coordinator.data
        return {
            "supply_fan_speed": data.get("supplyfan"),
            "auto_mode": bool(data.get("automode", 0)),
        }

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn on the fan, optionally setting speed."""
        try:
            await self._client.send_command(self._unit_id, CMD_POWER_ON)
            if preset_mode is not None:
                await self._set_preset(preset_mode)
            elif percentage is not None:
                await self._set_percentage(percentage)
        except MelViewError as err:
            _LOGGER.error("Failed to turn on Lossnay fan: %s", err)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the fan."""
        try:
            await self._client.send_command(self._unit_id, CMD_POWER_OFF)
        except MelViewError as err:
            _LOGGER.error("Failed to turn off Lossnay fan: %s", err)
        await self.coordinator.async_request_refresh()

    async def async_set_percentage(self, percentage: int) -> None:
        """Set fan speed by percentage."""
        try:
            await self._set_percentage(percentage)
        except MelViewError as err:
            _LOGGER.error("Failed to set Lossnay fan percentage: %s", err)
        await self.coordinator.async_request_refresh()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set fan speed by preset name."""
        try:
            await self._set_preset(preset_mode)
        except MelViewError as err:
            _LOGGER.error("Failed to set Lossnay fan preset: %s", err)
        await self.coordinator.async_request_refresh()

    async def _set_percentage(self, percentage: int) -> None:
        cmd_value = None
        for threshold, cmd in PERCENTAGE_TO_FAN_CMD:
            if percentage <= threshold:
                cmd_value = cmd
                break
        if cmd_value is None:
            cmd_value = PERCENTAGE_TO_FAN_CMD[-1][1]
        await self._client.send_command(self._unit_id, f"FS{cmd_value}")

    async def _set_preset(self, preset_mode: str) -> None:
        cmd_value = FAN_PRESET_TO_CMD.get(preset_mode)
        if cmd_value is None:
            _LOGGER.warning("Unknown preset mode: %s", preset_mode)
            return
        await self._client.send_command(self._unit_id, f"FS{cmd_value}")
