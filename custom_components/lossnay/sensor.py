"""Sensor entities for Mitsubishi Lossnay ERV."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import LossnayCoordinator
from .const import CONF_UNIT_ID, CONF_UNIT_NAME, DOMAIN


@dataclass(frozen=True)
class LossnaySensorDescription(SensorEntityDescription):
    """Describes a Lossnay sensor."""

    value_key: str = ""
    value_transform: Any = None  # optional callable


SENSOR_DESCRIPTIONS: tuple[LossnaySensorDescription, ...] = (
    LossnaySensorDescription(
        key="room_temp",
        name="Room Temperature",
        value_key="roomtemp",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    LossnaySensorDescription(
        key="outdoor_temp",
        name="Outdoor Temperature",
        value_key="outdoortemp",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    LossnaySensorDescription(
        key="supply_temp",
        name="Supply Temperature",
        value_key="supplytemp",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    LossnaySensorDescription(
        key="exhaust_temp",
        name="Exhaust Temperature",
        value_key="exhausttemp",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    LossnaySensorDescription(
        key="core_efficiency",
        name="Core Efficiency",
        value_key="coreefficiency",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:heat-wave",
        value_transform=lambda v: round(float(v) * 100, 1) if v is not None else None,
    ),
    LossnaySensorDescription(
        key="filter",
        name="Filter Status",
        value_key="changefilter",
        icon="mdi:air-filter",
        value_transform=lambda v: "replace" if v else "ok",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Lossnay sensor entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: LossnayCoordinator = data["coordinator"]
    unit_id: str = data["unit_id"]
    unit_name: str = entry.data[CONF_UNIT_NAME]

    async_add_entities(
        LossnaySensor(
            coordinator=coordinator,
            description=desc,
            unit_id=unit_id,
            unit_name=unit_name,
            entry_id=entry.entry_id,
        )
        for desc in SENSOR_DESCRIPTIONS
    )


class LossnaySensor(CoordinatorEntity[LossnayCoordinator], SensorEntity):
    """A single Lossnay sensor."""

    entity_description: LossnaySensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: LossnayCoordinator,
        description: LossnaySensorDescription,
        unit_id: str,
        unit_name: str,
        entry_id: str,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, unit_id)},
            "name": unit_name,
            "manufacturer": "Mitsubishi Electric",
            "model": "Lossnay ERV",
        }

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        raw = self.coordinator.data.get(self.entity_description.value_key)
        if raw is None:
            return None
        transform = self.entity_description.value_transform
        if transform is not None:
            return transform(raw)
        try:
            return float(raw)
        except (TypeError, ValueError):
            return raw
