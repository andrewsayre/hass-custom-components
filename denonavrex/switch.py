"""A switch to control the power state of Denon and Maranz comaptible AVRs."""
import asyncio
import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import CONF_HOST, CONF_HOSTS, CONF_NAME
from homeassistant.core import callback

from . import DOMAIN, SIGNAL_UPDATED, AvrManager
from .avrclient import AvrZone

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the switch platform."""
    switches = []
    manager = hass.data[DOMAIN][CONF_HOSTS][discovery_info[CONF_HOST]]
    name = discovery_info[CONF_NAME]
    for zone in manager.client.zones:
        switches.append(DenonAvrSwitch(manager, zone, name))

    async_add_entities(switches, True)


class DenonAvrSwitch(SwitchEntity):
    """Representation of a Denon/Maranz AVR power switch."""

    def __init__(self, manager: AvrManager, zone: AvrZone, name: str):
        """Init the switch."""
        self._manager = manager
        self._zone = zone
        self._name = f"{name} Zone {zone.zone_number}"
        self._signals = []

    @property
    def should_poll(self) -> bool:
        """Return True if entity has to be polled for state."""
        return False

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

    async def _schedule_delayed_update(self):
        """Update the state after a delay."""
        await asyncio.sleep(1.5)
        await self._manager.update()

    async def async_added_to_hass(self):
        """Entity added to hass."""

        @callback
        def _update(host):
            if host == self._manager.host:
                self.async_write_ha_state()

        self._signals.append(
            self.hass.helpers.dispatcher.async_dispatcher_connect(
                SIGNAL_UPDATED, _update
            )
        )

    async def async_will_remove_from_hass(self):
        """Prepare to be removed from hass."""
        for signal_remove in self._signals:
            signal_remove()
        self._signals.clear()
