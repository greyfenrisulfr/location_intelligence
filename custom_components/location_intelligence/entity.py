"""Shared entity helpers."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo, Entity

from .const import DOMAIN, NAME


class LocationIntelligenceEntity(Entity):
    """Base entity for this integration."""

    _attr_has_entity_name = True

    @property
    def device_info(self) -> DeviceInfo:
        """Describe the parent integration device."""

        return DeviceInfo(
            identifiers={(DOMAIN, DOMAIN)},
            manufacturer="greyfenrisulfr",
            name=NAME,
            entry_type=DeviceEntryType.SERVICE,
        )

