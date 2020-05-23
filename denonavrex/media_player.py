"""A media player representation of Denon and Maranz comaptible AVRs."""
import logging
from typing import Any, Dict, Optional

from homeassistant.components.media_player import MediaPlayerEntity
from homeassistant.const import CONF_HOST, CONF_HOSTS, CONF_NAME
from homeassistant.core import callback

from . import DOMAIN, SIGNAL_UPDATED, AvrManager

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the media player platform."""
    manager = hass.data[DOMAIN][CONF_HOSTS][discovery_info[CONF_HOST]]
    name = discovery_info[CONF_NAME]
    async_add_entities([DenonAvrMediaPlayer(manager, name)], True)


class DenonAvrMediaPlayer(MediaPlayerEntity):
    """Represents the main AVR media player entity."""

    def __init__(self, manager: AvrManager, name: str):
        """Init the media player."""
        self._manager = manager
        self._client = manager.client
        self._name = name
        self._signals = []

    @property
    def should_poll(self) -> bool:
        """Return True if entity has to be polled for state."""
        return False

    @property
    def name(self):
        """Return the name of the entity."""
        return self._name

    @property
    def device_state_attributes(self) -> Optional[Dict[str, Any]]:
        """Return device specific state attributes."""
        return {
            "all_zone_stereo_enabled": self._client.all_zone_stereo_enabled,
            "all_zone_stereo_zones": self._client.all_zone_stereo_zones,
        }

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
