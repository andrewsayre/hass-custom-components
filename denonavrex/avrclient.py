"""Define the AVR Client library."""
import logging
import xml.etree.ElementTree as ET

import aiohttp

URL_COMMAND = "/goform/AppCommand.xml"
URL_ZONE_TURN_OFF = "/goform/formiPhoneAppPower.xml?{zone}+PowerStandby"
URL_ZONE_TURN_ON = "/goform/formiPhoneAppPower.xml?{zone}+PowerOn"

STATUS_REQUEST = '<?xml version="1.0" encoding="utf-8" ?><tx><cmd id="1">GetAllZonePowerStatus</cmd><cmd id="2">GetAllZoneStereo</cmd></tx>'

HEADERS = {"Content-Type": "application/xml"}

ZONE_1 = 1
ZONE_2 = 2
ZONE_3 = 3
ZONE_4 = 4

_LOGGER = logging.getLogger(__name__)


class AvrClient:
    """Encapsulates the functionality of interfacing to the Avr."""

    def __init__(self, host: str, port: int, session: aiohttp.ClientSession):
        """Initialize the client."""
        self._host = host
        self._port = port
        self._base_url = f"http://{host}:{port}"
        self._session = session
        self._zones = []
        self._all_zone_stereo_enabled = False
        self._all_zone_stereo_zones = []

    @property
    def host(self):
        """Get the host of the AVR."""
        return self._host

    @property
    def zones(self):
        """Get the zones in the AVR."""
        return self._zones

    @property
    def all_zone_stereo_enabled(self):
        """Return True if the All Zone Stereo option is active."""
        return self._all_zone_stereo_enabled

    @property
    def all_zone_stereo_zones(self):
        """Return the zones enabled for All Zone Stereo."""
        return self._all_zone_stereo_zones

    async def update(self):
        """Obtain the latest state for the AVR."""
        url = self._base_url + URL_COMMAND.format(host=self._host, port=self._port)
        async with self._session.post(
            url, data=STATUS_REQUEST, headers=HEADERS
        ) as resp:
            if resp.status == 200:
                xml = ET.fromstring(await resp.text())

                # Process power status
                for index, data in enumerate(xml[0]):
                    zone_number = index + 1
                    if len(self._zones) < zone_number:
                        self._zones.append(AvrZone(zone_number, self))
                    zone = self._zones[index]
                    zone._is_on = data.text == "ON"

                # Process all zone stereo
                self._all_zone_stereo_enabled = xml[1].find("value").text == "1"
                self._all_zone_stereo_zones.clear()
                zones_text = xml[1].find("zones").text
                for zone_index, is_on in enumerate(zones_text):
                    if is_on == "1":
                        self._all_zone_stereo_zones.append(zone_index + 2)

    async def get_request(self, url: str):
        """Perform a GET request to the AVR."""
        async with self._session.get(self._base_url + url) as resp:
            return resp.status


class AvrZone:
    """Represents an individual zone of the AVR."""

    def __init__(self, zone_number, client: AvrClient):
        """Initialize the zone."""
        self._zone_number = zone_number
        self._client = client
        self._is_on = False

    @property
    def is_on(self) -> bool:
        """Return true if it is on."""
        return self._is_on

    @property
    def zone_number(self) -> int:
        """Return the number of the zone."""
        return self._zone_number

    async def set_power_state(self, state: bool):
        """Set the power state."""
        url = (URL_ZONE_TURN_ON if state else URL_ZONE_TURN_OFF).format(
            zone=self._zone_number
        )
        return await self._client.get_request(url)

    async def update(self):
        """Update the state of the zone."""
        await self._client.update()
