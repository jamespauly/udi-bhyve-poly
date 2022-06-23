import logging
import json
import aiohttp

from aiohttp import WSMsgType
from asyncio import ensure_future
from math import ceil

_LOGGER = logging.getLogger(__name__)

STATE_STARTING = "starting"
STATE_RUNNING = "running"
STATE_STOPPED = "stopped"

RECONNECT_DELAY = 5

# pylint: disable=too-many-instance-attributes
class OrbitWebsocket:
    """
        Websocket transport, session handling, message generation.
        Inspired by https://github.com/Kane610/deconz/blob/master/pydeconz/websocket.py
    """

    # pylint: disable=too-many-arguments
    def __init__(self, token, loop, session, url, async_callback):
        """Create resources for websocket communication."""
        self._token = token
        self._loop = loop
        self._session = session
        self._url = url
        self._async_callback = async_callback
        self._state = None

        self._heartbeat_cb = None
        self._heartbeat = 25
        self._ws = None

    def _cancel_heartbeat(self) -> None:
        if self._heartbeat_cb is not None:
            self._heartbeat_cb.cancel()
            self._heartbeat_cb = None

    def _reset_heartbeat(self) -> None:
        self._cancel_heartbeat()

        when = ceil(self._loop.time() + self._heartbeat)
        self._heartbeat_cb = self._loop.call_at(when, self._send_heartbeat)

    def _send_heartbeat(self) -> None:
        if not self._ws.closed:
            # fire-and-forget a task is not perfect but maybe ok for
            # sending ping. Otherwise we need a long-living heartbeat
            # task in the class.
            self._loop.create_task(self._ping())

    async def _ping(self):
        await self._ws.send_str(json.dumps({"event": "ping"}))
        self._reset_heartbeat()

    @property
    def state(self):
        """ Returns the state of the websocket. """
        return self._state

    @state.setter
    def state(self, value):
        self._state = value

    def start(self):
        """ Start the websocket. """
        if self.state != STATE_RUNNING:
            self.state = STATE_STARTING
        self._loop.create_task(self.running())

    async def running(self):
        """Start websocket connection."""

        try:
            if self._ws is None or self._ws.closed or self.state != STATE_RUNNING:
                async with self._session.ws_connect(self._url) as self._ws:
                    _LOGGER.info("Authenticating websocket")
                    await self._ws.send_str(
                        json.dumps(
                            {
                                "event": "app_connection",
                                "orbit_session_token": self._token,
                            }
                        )
                    )

                    _LOGGER.info("Websocket connected")

                    self._reset_heartbeat()

                    self.state = STATE_RUNNING

                    while True:
                        msg = await self._ws.receive()
                        self._reset_heartbeat()
                        _LOGGER.debug("msg received {}".format(str(msg)[:80]))

                        if self.state == STATE_STOPPED:
                            break

                        elif msg.type == WSMsgType.TEXT:
                            ensure_future(self._async_callback(json.loads(msg.data)))

                        elif msg.type == WSMsgType.PING:
                            self._ws.pong()

                        # elif msg.type == WSMsgType.CLOSE:
                        #     await self._ws.close()
                        #     break

                        elif msg.type == WSMsgType.CLOSED:
                            _LOGGER.error("websocket connection closed")
                            break

                        elif msg.type == WSMsgType.ERROR:
                            _LOGGER.error("websocket error %s", self._ws.exception())
                            break

                    if self._ws.closed:
                        _LOGGER.info("Websocket closed? %s", self._ws.closed)

                    if self._ws.exception():
                        _LOGGER.warning("Websocket exception: %s", self._ws.exception())

        except aiohttp.ClientConnectorError:
            _LOGGER.error("Client connection error")
            if self.state != STATE_STOPPED:
                self.retry()

        # pylint: disable=broad-except
        except Exception as err:
            _LOGGER.error("Unexpected error %s", err)
            if self.state != STATE_STOPPED:
                self.retry()

        else:
            if self.state != STATE_STOPPED:
                _LOGGER.info("Reconnecting websocket; state: %s", self.state)
                self.retry()

    async def stop(self):
        """Close websocket connection."""
        self.state = STATE_STOPPED
        _LOGGER.info("Closing websocket connection")
        await self._ws.close()

    def retry(self):
        """Retry to connect to Orbit."""
        if self.state != STATE_STARTING:
            self.state = STATE_STARTING
            self._loop.call_later(RECONNECT_DELAY, self.start)
            _LOGGER.info("Reconnecting to Orbit in %i.", RECONNECT_DELAY)

    async def send(self, payload):
        """Send a websocket message."""
        if not self._ws.closed:
            await self._ws.send_str(json.dumps(payload))
        else:
            _LOGGER.warning("Tried to send message whilst websocket closed")