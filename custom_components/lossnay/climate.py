"""Climate entity for Mitsubishi Lossnay ERV (heat exchange mode control)."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
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
    HVAC_TO_MODE_CMD,
    MODE_TO_HVAC,
)

_LOGGER = logging.getLogger(__name__)

_HVAC_MODES = [HVACMode.HEAT, HVACMode.AUTO, HVACMode.FAN_ONLY, HVACMode.OFF]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Lossnay climate entity."""
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            LossnayClimate(
                coordinator=data["coordinator"],
                client=data["client"],
                unit_id=data["unit_id"],
                unit_name=entry.data[CONF_UNIT_NAME],
                entry_id=entry.entry_id,
            )
        ]
    )


class LossnayClimate(CoordinatorEntity[LossnayCoordinator], ClimateEntity):
    """Climate entity representing the Lossnay heat exchange mode."""

    _attr_has_entity_name = True
    _attr_name = "Mode"
    _attr_hvac_modes = _HVAC_MODES
    _attr_supported_features = ClimateEntityFeature.TURN_ON | ClimateEntityFeature.TURN_OFF
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    # ERV has no temperature setpoint
    _attr_target_temperature = None
    _attr_target_temperature_step = None
    _attr_min_temp = None
    _attr_max_temp = None

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
        self._attr_unique_id = f"{entry_id}_climate"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, unit_id)},
            "name": unit_name,
            "manufacturer": "Mitsubishi Electric",
            "model": "Lossnay ERV",
        }

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current HVAC mode."""
        if not self.coordinator.data.get("power", 0):
            return HVACMode.OFF
        setmode = self.coordinator.data.get("setmode")
        if setmode is None:
            return HVACMode.OFF
        ha_mode = MODE_TO_HVAC.get(int(setmode))
        if ha_mode == "heat":
            return HVACMode.HEAT
        if ha_mode == "auto":
            return HVACMode.AUTO
        if ha_mode == "fan_only":
            return HVACMode.FAN_ONLY
        return HVACMode.OFF

    @property
    def current_temperature(self) -> float | None:
        """Return the room temperature."""
        temp = self.coordinator.data.get("roomtemp")
        if temp is None:
            return None
        try:
            return float(temp)
        except (TypeError, ValueError):
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        data = self.coordinator.data
        return {
            "auto_mode": bool(data.get("automode", 0)),
            "outdoor_temp": data.get("outdoortemp"),
            "supply_temp": data.get("supplytemp"),
            "exhaust_temp": data.get("exhausttemp"),
            "core_efficiency": data.get("coreefficiency"),
            "change_filter": bool(data.get("changefilter", 0)),
            "fault": data.get("fault", ""),
        }

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set the HVAC mode (heat exchange mode)."""
        try:
            if hvac_mode == HVACMode.OFF:
                await self._client.send_command(self._unit_id, CMD_POWER_OFF)
            else:
                # Ensure unit is on
                if not self.coordinator.data.get("power", 0):
                    await self._client.send_command(self._unit_id, CMD_POWER_ON)
                mode_str = hvac_mode.value  # "heat", "auto", "fan_only"
                cmd = HVAC_TO_MODE_CMD.get(mode_str)
                if cmd:
                    await self._client.send_command(self._unit_id, cmd)
                else:
                    _LOGGER.warning("No command mapping for HVAC mode: %s", hvac_mode)
        except MelViewError as err:
            _LOGGER.error("Failed to set Lossnay HVAC mode: %s", err)
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self) -> None:
        """Turn on the unit."""
        try:
            await self._client.send_command(self._unit_id, CMD_POWER_ON)
        except MelViewError as err:
            _LOGGER.error("Failed to turn on Lossnay: %s", err)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self) -> None:
        """Turn off the unit."""
        try:
            await self._client.send_command(self._unit_id, CMD_POWER_OFF)
        except MelViewError as err:
            _LOGGER.error("Failed to turn off Lossnay: %s", err)
        await self.coordinator.async_request_refresh()
