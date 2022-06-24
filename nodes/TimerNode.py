import json
import udi_interface

LOGGER = udi_interface.LOGGER
Custom = udi_interface.Custom

class TimerNode(udi_interface.Node):
    def __init__(self, polyglot, primary, address, name, device):
        super(TimerNode, self).__init__(polyglot, primary, address, name)
        LOGGER.debug("Initialize TimerNode")
        self.poly = polyglot
        self.name = name
        self.primary = primary
        self.address = address
        self.device = device
        self.poly.subscribe(self.poly.START, self.start, address)
        self.poly.subscribe(self.poly.POLL, self.poll)

    def poll(self, pollType):
        if 'shortPoll' in pollType:
            LOGGER.info('shortPoll (Updating Data)')
            self.query()
        else:
            pass

    def start(self):
        LOGGER.debug("TimerNode - start")
        LOGGER.info('Address of current Node ' + self.address)
        LOGGER.debug('start ' + json.dumps(self.device))
        self.update(self.device)

    def query(self):
        self.update(self.device)

    def update(self, device):
        LOGGER.info(f'Updating device {json.dumps(device)}')
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

    id = 'timernode'

    drivers = [{'driver': 'GV1', 'value': 0, 'uom': '51'},
               {'driver': 'GV2', 'value': 0, 'uom': '105'},
               {'driver': 'GV3', 'value': 0, 'uom': '48'},
               {'driver': 'GV4', 'value': 0, 'uom': '17'},
               {'driver': 'GV5', 'value': 0, 'uom': '56'},
               {'driver': 'GV6', 'value': 0, 'uom': '56'},
               {'driver': 'GV7', 'value': 0, 'uom': '25'}]
