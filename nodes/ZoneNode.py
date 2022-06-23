import json
import udi_interface
import asyncio
from aiohttp import ClientSession

from nodes import ZoneNode
from pybhyve import Client
from pybhyve.errors import BHyveError

LOGGER = udi_interface.LOGGER
Custom = udi_interface.Custom

class ZoneNode(udi_interface.Node):
    def __init__(self, polyglot, primary, address, name):
        super(ZoneNode, self).__init__(polyglot, primary, address, name)
        LOGGER.debug("Initialize TimerNode")
        self.poly = polyglot
        self.name = name
        self.primary = primary
        self.address = address
        self.poly.subscribe(self.poly.CUSTOMPARAMS, self.parameterHandler)
        self.poly.subscribe(self.poly.START, self.start, address)
        self.poly.subscribe(self.poly.POLL, self.poll)

    def poll(self, pollType):
        if 'shortPoll' in pollType:
            LOGGER.info('shortPoll (Updating Data)')
            self.query()
        else:
            pass

    def parameterHandler(self, params):
        self.Parameters.load(params)
        self.user = self.Parameters['username']
        self.password = self.Parameters['password']

    def start(self):
        LOGGER.debug("TimerNode - start")

    def query(self):
        LOGGER.debug('TimerNode - query')
        pass

    def load_zones(self, device) -> None:
        for zone in device['zones']:
            self.poly.addNode(ZoneNode(self.poly, self.address, zone['station'], zone['name']))
            LOGGER.debug("Zone: %s", json.dumps(zone))

    async def get_device(self, user, password) -> None:
        async with ClientSession() as session:
            try:
                client = Client(user, password, asyncio.get_event_loop(), session, None)
                await client.login()
                devices = await client.devices
                for device in devices:
                    if device['reference'] == self.address:
                        LOGGER.debug(f"Getting Device with Reference {device['reference']} and ID {device['id']}")
                        return device
            except BHyveError as err:
                LOGGER.error("There was an error in load_timers: %s", err)
                return None

    def update(self, device):
        LOGGER.debug(f'Updating device {json.dumps(device)}')
        total_zones = device['num_stations']
        active_num_of_zones = len(device['zones'])
        current_watering_status = device['status']['watering_status']
        precip_prob = device['weather_delay_thresholds']['precip_prob']
        precip_in = device['weather_delay_thresholds']['precip_in']
        wind_speed_mph = device['weather_delay_thresholds']['wind_speed_mph']
        freeze_temp_f = device['weather_delay_thresholds']['freeze_temp_f']

        self.setDriver('GV1', precip_prob, True)
        self.setDriver('GV2', precip_in, True)
        self.setDriver('GV3', wind_speed_mph, True)
        self.setDriver('GV4', freeze_temp_f, True)
        self.setDriver('GV5', total_zones, True)
        self.setDriver('GV6', active_num_of_zones, True)
        self.setDriver('GV7', current_watering_status, True)

    id = 'zonenode'

    drivers = [{'driver': 'GV1', 'value': 0, 'uom': '51'},
               {'driver': 'GV2', 'value': 0, 'uom': '105'},
               {'driver': 'GV3', 'value': 0, 'uom': '48'},
               {'driver': 'GV4', 'value': 0, 'uom': '17'},
               {'driver': 'GV5', 'value': 0, 'uom': '56'},
               {'driver': 'GV6', 'value': 0, 'uom': '56'},
               {'driver': 'GV7', 'value': 0, 'uom': '25'}]
