# !/usr/bin/env python
import time
import json
import asyncio

from aiohttp import ClientSession

import udi_interface

from nodes import TimerNode
from pybhyve import Client
from pybhyve.errors import BHyveError

LOGGER = udi_interface.LOGGER
Custom = udi_interface.Custom


class BHyveController(udi_interface.Node):
    def __init__(self, polyglot, primary, address, name):
        super(BHyveController, self).__init__(polyglot, primary, address, name)
        self.poly = polyglot
        self.name = name
        self.primary = primary
        self.address = address
        self.configured = False
        self.nodesAddedCount = 0
        self.deviceCount = 0

        self.Notices = Custom(polyglot, 'notices')
        self.Parameters = Custom(polyglot, 'customparams')

        self.poly.subscribe(self.poly.CUSTOMPARAMS, self.parameterHandler)
        self.poly.subscribe(self.poly.START, self.start, address)
        self.poly.subscribe(self.poly.POLL, self.poll)
        self.poly.subscribe(self.poly.ADDNODEDONE, self.nodeHandler)

        self.poly.ready()
        self.poly.addNode(self)

    def start(self):
        self.poly.updateProfile()
        self.poly.setCustomParamsDoc()
        self.query()
        LOGGER.info('Started udi-bhyve-poly NodeServer')

    def nodeHandler(self, data):
        self.nodesAddedCount += 1

    def parameterHandler(self, params):
        self.Parameters.load(params)

        userValid = False
        passwordValid = False

        user = self.Parameters['username']
        password = self.Parameters['password']

        if user is not None and len(user) > 0:
            userValid = True
        else:
            LOGGER.error('User is Blank')

        if password is not None and len(password) > 0:
            passwordValid = True
        else:
            LOGGER.error('Password is Blank')

        self.Notices.clear()

        if userValid and passwordValid:
            self.configured = True
            self.query()
        else:
            if not userValid:
                self.Notices['user'] = 'User must be configured.'
            if not passwordValid:
                self.Notices['password'] = 'Password must be configured.'

    def poll(self, pollType):
        if 'shortPoll' in pollType:
            LOGGER.info('shortPoll (controller)')
            self.query()
        else:
            LOGGER.info('longPoll (controller)')
            pass

    def query(self, command=None):
        self.discover()
        LOGGER.info('BHyveController - query')

    def discover(self, *args, **kwargs):
        user = self.Parameters['user']
        password = self.Parameters['password']
        try:
            LOGGER.info("Starting BHyve Timer Device Discovery")
            asyncio.run(self.load_timers(user, password))
        except Exception as ex:
            LOGGER.error("BHyveController - Discovery failed with error", ex)

    async def load_timers(self, user, password) -> None:
        async with ClientSession() as session:
            try:
                client = Client(user, password, asyncio.get_event_loop(), session, None)
                await client.login()
                devices = await client.devices
                for device in devices:
                    self.poly.addNode(TimerNode(self.poly, self.address, device['reference'], device['name']))
                    LOGGER.info("Device: %s", json.dumps(device))
            except BHyveError as err:
                LOGGER.error("There was an error in load_timers: %s", err)

    def delete(self):
        LOGGER.info('Deleting BHyve Node Server')

    def stop(self):
        LOGGER.info('Stopping BHyve NodeServer.')

    def remove_notices_all(self, command):
        self.Notices.clear()

    id = 'bhyve'
    commands = {'QUERY': query, 'REMOVE_NOTICES_ALL': remove_notices_all, 'DISCOVER': discover}
    drivers = [{'driver': 'ST', 'value': 1, 'uom': 2}]
