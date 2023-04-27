#!/bin/python3

import yaml
import asyncio
import signal
import select
import threading
import websockets

import lcm
from mbot_bridge.utils import type_utils
from mbot_bridge.utils.json_helpers import (
    MBotJSONRequest, MBotJSONResponse, MBotJSONError,
    MBotRequestType, BadMBotRequestError
)


class LCMMessageQueue(object):
    def __init__(self, channel, dtype, queue_size=1):
        self.channel = channel
        self.dtype = dtype
        self.queue_size = queue_size

        self._queue = []
        self._lock = threading.Lock()

    def push(self, msg, decode=True):
        # Decode to LCM type.
        if decode:
            msg = type_utils.decode(msg, self.dtype)

        self._lock.acquire()
        # Add the current message to the back of the queue.
        self._queue.append(msg)
        # Remove old messages if necessary.
        while len(self._queue) > self.queue_size:
            self._queue.pop(0)
        self._lock.release()

    def latest(self):
        latest = None
        self._lock.acquire()
        if len(self._queue) > 0:
            latest = self._queue[-1]
        self._lock.release()
        return latest

    def pop(self):
        first = None
        self._lock.acquire()
        if len(self._queue) > 0:
            first = self._queue.pop(0)
        self._lock.release()
        return first


class MBotBridgeServer(object):
    def __init__(self, lcm_address, subs=[], lcm_timeout=1000):
        self._lcm_timeout = lcm_timeout  # This is how long to timeout in the LCM handle call.
        self._lcm = lcm.LCM(lcm_address)

        self._msg_managers = {}
        for channel in subs:
            ch, lcm_type = channel["channel"], channel["type"]
            self._msg_managers.update({channel["channel"]: LCMMessageQueue(ch, lcm_type)})
            self._lcm.subscribe(ch, self.listener)

        self._running = True
        self._lock = threading.Lock()

    def stop(self, *args):
        self._lock.acquire()
        self._running = False
        self._lock.release()

    def running(self):
        self._lock.acquire()
        res = self._running
        self._lock.release()
        return res

    def listener(self, channel, data):
        self._msg_managers[channel].push(data, decode=True)

    def handleOnce(self):
        # This is a non-blocking handle, which only calls handle if a message is ready.
        rfds, wfds, efds = select.select([self._lcm.fileno()], [], [], 0)
        if rfds:
            self._lcm.handle()

    def lcm_loop(self):
        while self.running():
            # This will block for a maximum of _lcm_timeout milliseconds, so it
            # might slow stopping the server, but it's less expensive than using
            # the non-blocking handleOnce.
            self._lcm.handle_timeout(self._lcm_timeout)

    async def handler(self, websocket):
        async for message in websocket:
            try:
                message = MBotJSONRequest(message)
            except BadMBotRequestError as e:
                # If something went wrong parsing this request, send the error message then continue.
                msg = f"Bad MBot request. Ignoring. BadMBotRequestError: {e}"
                print(msg)
                err = MBotJSONError(msg)
                await websocket.send(err.as_json())
                continue

            if message.type() == MBotRequestType.REQUEST:
                ch = message.channel()
                if ch not in self._msg_managers:
                    # If the channel being requested does not exist, return an error.
                    msg = f"Bad MBot request. No channel: {ch}"
                    print(msg)
                    err = MBotJSONError(msg)
                    await websocket.send(err.as_json())
                else:
                    # Get the newest data.
                    latest = self._msg_managers[ch].latest()
                    latest = type_utils.lcm_type_to_dict(latest)  # Convert to dictionary.
                    # Wrap the response data for sending over the websocket.
                    res = MBotJSONResponse(ch, latest, self._msg_managers[ch].dtype)
                    await websocket.send(res.as_json())
            elif message.type() == MBotRequestType.PUBLISH:
                try:
                    # Publish the data sent over the websocket.
                    pub_msg = type_utils.dict_to_lcm_type(message.data, message.dtype)
                    self._lcm.publish(message.channel(), pub_msg.encode())
                except AttributeError as e:
                    # If the type or data is bad, send back an error message.
                    msg = (f"Bad MBot publish. Bad message type ({message.dtype}) or data (\"{message.data}\"). "
                           f"AttributeError: {e}")
                    print(msg)
                    err = MBotJSONError(msg)
                    await websocket.send(err.as_json())


async def main(args):
    with open(args.config, 'r') as f:
        config = yaml.load(f, Loader=yaml.Loader)

    # Set the stop condition when receiving SIGTERM or SIGINT.
    loop = asyncio.get_running_loop()
    stop = asyncio.Future()
    loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)
    loop.add_signal_handler(signal.SIGINT, stop.set_result, None)

    lcm_manager = MBotBridgeServer(config["lcm_address"], config["subs"])

    # Not awaiting the task will cause it to be stoped when the loop ends.
    asyncio.create_task(asyncio.to_thread(lcm_manager.lcm_loop))

    async with websockets.serve(
        lcm_manager.handler,
        host="",
        port=5000,
        reuse_port=True,
    ):
        await stop
        lcm_manager.stop()

    print("MBot Bridge: Exited cleanly.")


def load_args(conf="config/default.yml"):
    parser = argparse.ArgumentParser(description="MBot Bridge Server.")
    parser.add_argument("--config", type=str, default=conf, help="Configuration file.")

    args = parser.parse_args()

    return args


if __name__ == "__main__":
    import argparse
    import importlib.resources as pkg_resources
    from . import config

    DEFAULT_CONFIG = pkg_resources.path(config, 'default.yml')

    args = load_args(DEFAULT_CONFIG)
    asyncio.run(main(args))
