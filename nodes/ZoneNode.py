import json
import udi_interface

LOGGER = udi_interface.LOGGER
Custom = udi_interface.Custom

class ZoneNode(udi_interface.Node):
    def __init__(self, polyglot, primary, address, name, zone):
        super(ZoneNode, self).__init__(polyglot, primary, address, name)
        LOGGER.debug("Initialize ZodeNode")
        self.poly = polyglot
        self.name = name
        self.primary = primary
        self.address = address
        self.zone = zone
        self.poly.subscribe(self.poly.START, self.start, address)
        self.poly.subscribe(self.poly.POLL, self.poll)

    def poll(self, pollType):
        if 'shortPoll' in pollType:
            LOGGER.info('shortPoll (Updating Data)')
            self.query()
        else:
            pass

    def start(self):
        LOGGER.debug("ZodeNode - start")
        LOGGER.info('Address of current Node ' + self.address)
        LOGGER.debug('start ' + json.dumps(self.zone))
        self.update(self.zone)

    def query(self):
        self.update(self.zone)

    def update(self, zone):
        sprinker_type_idx = 3
        LOGGER.info(f'Updating zone {json.dumps(zone)}')
        station = zone['station']
        sprinker_type = zone['sprinkler_type']
        if 'drip' in sprinker_type:
            sprinker_type_idx = 1
        elif 'spray' in sprinker_type:
            sprinker_type_idx = 0
        elif 'rotor' in sprinker_type:
            sprinker_type_idx = 2
        else:
            sprinker_type_idx = 3
        smart_watering_enabled = zone['smart_watering_enabled']

        self.setDriver('GV1', station, True)
        self.setDriver('GV2', sprinker_type_idx, True)
        self.setDriver('GV3', smart_watering_enabled, True)

    id = 'zonenode'

    drivers = [{'driver': 'GV1', 'value': 0, 'uom': '56'},
               {'driver': 'GV2', 'value': 0, 'uom': '25'},
               {'driver': 'GV3', 'value': 0, 'uom': '2'}]
