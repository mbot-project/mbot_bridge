#!/bin/python3

import yaml
import json
import asyncio
import signal
import select
import threading
import websockets

import lcm
from mbot_bridge.utils import type_utils
from mbot_bridge.utils.json_helpers import MBotJSONRequest, MBotRequestType, BadMBotRequestError


class LCMMessageQueue(object):
    def __init__(self, channel, lcm_type, queue_size=1):
        self.channel = channel
        self.lcm_type = lcm_type
        self.queue_size = queue_size

        self._queue = []
        self._lock = threading.Lock()

    def push(self, msg, decode=True):
        # Decode to LCM type.
        if decode:
            msg = type_utils.decode(msg, self.lcm_type)

        self._lock.acquire()
        # Add the current message to the back of the queue.
        self._queue.append(msg)
        # Remove old messages if necessary.
        while len(self._queue) > self.queue_size:
            self._queue.pop(0)
        self._lock.release()

    def latest(self, as_json=False):
        latest = None
        self._lock.acquire()
        if len(self._queue) > 0:
            latest = self._queue[-1]
        self._lock.release()
        if as_json and latest is not None:
            latest = type_utils.lcm_type_to_dict(latest)
        return latest

    def pop(self):
        first = None
        self._lock.acquire()
        if len(self._queue) > 0:
            first = self._queue.pop(0)
        self._lock.release()
        return first


class MBotBridgeServer(object):
    def __init__(self, lcm_address, subs=[]):
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
            self.handleOnce()

    async def handler(self, websocket):
        async for message in websocket:
            try:
                message = MBotJSONRequest(message)
            except BadMBotRequestError as e:
                print("Bad MBot request. Ignoring. BadMBotRequestError:", e)
                continue

            print("Got WS msg!", message)

            if message.type() == MBotRequestType.REQUEST:
                ch = message.channel()
                if ch not in self._msg_managers:
                    # TODO: Send back an error.
                    print("Bad request: No channel", ch)
                    continue

                latest = self._msg_managers[ch].latest(as_json=True)
                # TODO: Wrap response.
                response = {"type": "response", "channel": ch, "data": latest}
                await websocket.send(json.dumps(response))


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


def load_args():
    parser = argparse.ArgumentParser(description="MBot Bridge Server.")
    parser.add_argument("--config", type=str, default="config/default.yml", help="Configuration file.")

    args = parser.parse_args()

    return args


if __name__ == "__main__":
    import argparse

    args = load_args()
    asyncio.run(main(args))
