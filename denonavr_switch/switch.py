"""A switch to control the power state of Denon and Maranz comaptible AVRs."""

import logging
import xml.etree.ElementTree as ET
from typing import Optional

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.switch import PLATFORM_SCHEMA, SwitchDevice
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.helpers.aiohttp_client import async_get_clientsession

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
    async_add_entities(switch, True)


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
        session = async_get_clientsession(self.hass)
        async with session.get(
            URL_TURN_ON.format(host=self._host, port=self._port)
        ) as response:
            if response.status == 200:
                self.async_update_ha_state(True)
            else:
                _LOGGER.error("Unable to turn device on: " + response)

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        session = async_get_clientsession(self.hass)
        async with session.get(
            URL_TURN_OFF.format(host=self._host, port=self._port)
        ) as response:
            if response.status == 200:
                self.async_update_ha_state(True)
            else:
                _LOGGER.error("Unable to turn device on: " + response)

    async def async_update(self):
        """Parse the data for this switch."""
        session = async_get_clientsession(self.hass)
        url = URL_POWER_STATUS.format(host=self._host, port=self._port)
        data = '<?xml version="1.0" encoding="utf-8" ?><tx><cmd id="1">GetAllZonePowerStatus</cmd></tx>'
        headers = {"Content-Type": "application/xml"}

        async with session.post(url, text=data, headers=headers) as resp:
            if resp.status == 200:
                xml = ET.parse(await resp.text())
                self._is_on = xml.getroot()[0][0].text == "ON"
            else:
                _LOGGER.error("Unable to get device power status: " + resp)
