"""A switch to control the power state of Denon and Maranz comaptible AVRs."""
import asyncio
import logging
import xml.etree.ElementTree as ET
from typing import Optional

import voluptuous as vol
from homeassistant.components.switch import PLATFORM_SCHEMA, SwitchDevice
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv

URL_TURN_OFF = "http://{host}:{port}/goform/formiPhoneAppDirect.xml?PWSTANDBY"
URL_TURN_ON = "http://{host}:{port}/goform/formiPhoneAppDirect.xml?PWON"
URL_POWER_STATUS = "http://{host}:{port}/goform/AppCommand.xml"

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_PORT, default=8080): cv.port,
    }
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the switch platform."""
    switch = DenonAvrSwitch(config[CONF_NAME], config[CONF_HOST], config[CONF_PORT])
    async_add_entities([switch], True)


class DenonAvrSwitch(SwitchDevice):
    """Representation of a Denon/Maranz AVR power switch."""

    def __init__(self, name: str, host: str, port: int):
        """Init the switch."""
        self._is_on = False
        self._name = name
        self._host = host
        self._port = port

    @property
    def is_on(self) -> bool:
        """Return true if it is on."""
        return self._is_on

    @property
    def name(self) -> Optional[str]:
        """Return the name of the entity."""
        return self._name

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        await self._set_state(True)

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        await self._set_state(False)

    async def async_update(self):
        """Parse the data for this switch."""
        session = async_get_clientsession(self.hass)
        url = URL_POWER_STATUS.format(host=self._host, port=self._port)
        data = '<?xml version="1.0" encoding="utf-8" ?><tx><cmd id="1">GetAllZonePowerStatus</cmd></tx>'
        headers = {"Content-Type": "application/xml"}
        async with session.post(url, data=data, headers=headers) as resp:
            if resp.status == 200:
                xml = ET.fromstring(await resp.text())
                self._is_on = xml[0][0].text == "ON"
            else:
                _LOGGER.error("Unable to get device power status: %s", resp)

    async def _set_state(self, state: bool):
        """Set the state of the switch."""
        session = async_get_clientsession(self.hass)
        url = (URL_TURN_ON if state else URL_TURN_OFF).format(
            host=self._host, port=self._port
        )
        async with session.get(url) as resp:
            if resp.status == 200:
                self.hass.async_create_task(self._schedule_delayed_update())
            else:
                _LOGGER.error("Unable to set device state: %s", resp)

    async def _schedule_delayed_update(self):
        """Update the state after a delay."""
        await asyncio.sleep(1.5)
        await self.async_update_ha_state(True)
