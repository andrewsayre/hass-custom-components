"""A switch to control the power state of Denon and Maranz comaptible AVRs."""
import asyncio
import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import CONF_HOST, CONF_HOSTS, CONF_NAME

from . import DOMAIN
from .avrclient import AvrZone

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the switch platform."""
    switches = []
    client = hass.data[DOMAIN][CONF_HOSTS][discovery_info[CONF_HOST]]
    name = discovery_info[CONF_NAME]
    for zone in client.zones:
        switches.append(DenonAvrSwitch(zone, name))

    async_add_entities(switches, True)


class DenonAvrSwitch(SwitchEntity):
    """Representation of a Denon/Maranz AVR power switch."""

    def __init__(self, zone: AvrZone, name: str):
        """Init the switch."""
        self._zone = zone
        self._name = f"{name} Zone {zone.zone_number}"

    @property
    def is_on(self) -> bool:
        """Return true if it is on."""
        return self._zone.is_on

    @property
    def name(self):
        """Return the name of the entity."""
        return self._name

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        await self._zone.set_power_state(True)
        self.hass.async_create_task(self._schedule_delayed_update())

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        await self._zone.set_power_state(False)
        self.hass.async_create_task(self._schedule_delayed_update())

    async def async_update(self):
        """Parse the data for this switch."""
        await self._zone.update()

    async def _schedule_delayed_update(self):
        """Update the state after a delay."""
        await asyncio.sleep(1.5)
        await self.async_update_ha_state(True)
