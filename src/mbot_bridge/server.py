#!/bin/python3

import yaml
import asyncio
import signal
import select
import logging
import threading
import websockets

import lcm
from mbot_bridge.utils import type_utils
from mbot_bridge.utils.json_messages import (
    MBotJSONMessage, MBotJSONResponse, MBotJSONError,
    MBotMessageType, BadMBotRequestError
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

    def empty(self):
        return len(self._queue) == 0


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

        logging.info(f"Connecting to LCM on address: {lcm_address}")
        logging.info("Listening on channels:")
        for ch in subs:
            logging.info(f"    {ch['channel']} ({ch['type']})")
        logging.info("MBot Bridge Server running!")

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
        logging.debug(f"Websocket connected with ID: {websocket.id}")

        # Handle all incoming messages from the websocket.
        async for message in websocket:
            logging.debug(f"Message from WS {websocket.id}: {message}")
            try:
                request = MBotJSONMessage(message, from_json=True)
            except BadMBotRequestError as e:
                # If something went wrong parsing this request, send the error message then continue.
                msg = f"Bad MBot request. Ignoring. BadMBotRequestError: {e}"
                logging.warning(f"{websocket.id} - {msg}")
                err = MBotJSONError(msg)
                await websocket.send(err.encode())
                continue

            if request.type() == MBotMessageType.REQUEST:
                ch = request.channel()
                if ch not in self._msg_managers:
                    # If the channel being requested does not exist, return an error.
                    msg = f"Bad MBot request. No channel: {ch}"
                    logging.warning(f"{websocket.id} - {msg}")
                    err = MBotJSONError(msg)
                    await websocket.send(err.encode())
                elif self._msg_managers[ch].empty():
                    msg = f"No data on channel: {ch}"
                    logging.warning(f"{websocket.id} - {msg}")
                    err = MBotJSONError(msg)
                    await websocket.send(err.encode())
                else:
                    # Get the newest data.
                    latest = self._msg_managers[ch].latest()
                    latest = type_utils.lcm_type_to_dict(latest)  # Convert to dictionary.
                    # Wrap the response data for sending over the websocket.
                    res = MBotJSONResponse(latest, ch, self._msg_managers[ch].dtype)
                    await websocket.send(res.encode())
            elif request.type() == MBotMessageType.PUBLISH:
                try:
                    # Publish the data sent over the websocket.
                    pub_msg = type_utils.dict_to_lcm_type(request.data(), request.dtype())
                    self._lcm.publish(request.channel(), pub_msg.encode())
                except AttributeError as e:
                    # If the type or data is bad, send back an error message.
                    msg = (f"Bad MBot publish. Bad message type ({request.dtype()}) or data (\"{request.data()}\"). "
                           f"AttributeError: {e}")
                    logging.warning(f"{websocket.id} - {msg}")
                    err = MBotJSONError(msg)
                    await websocket.send(err.encode())


async def main(args):
    logging.info(f"Reading configuration from: {args.config}")
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
        port=args.port,
        reuse_port=True,
    ):
        await stop
        lcm_manager.stop()

    logging.info("MBot Bridge exited cleanly.")


def load_args(conf="config/default.yml"):
    parser = argparse.ArgumentParser(description="MBot Bridge Server.")
    parser.add_argument("--config", type=str, default=conf, help="Configuration file.")
    parser.add_argument("--port", type=int, default=5005, help="Websocket port.")
    parser.add_argument("--log-file", type=str, default="mbot_bridge_server.log", help="Log file.")
    parser.add_argument("--log", type=str, default="INFO", help="Log level.")
    parser.add_argument("--max-log-size", type=int, default=2 * 1024 * 1024, help="Max log size.")

    args = parser.parse_args()

    # Turn the logging level into the correct form.
    numeric_level = getattr(logging, args.log.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {args.log}')
    args.log = numeric_level

    return args


if __name__ == "__main__":
    import os
    import argparse
    from . import config
    from logging import handlers

    DEFAULT_CONFIG = os.path.join(config.__path__[0], 'default.yml')

    args = load_args(DEFAULT_CONFIG)

    # Setup logging.
    file_handler = handlers.RotatingFileHandler(args.log_file, maxBytes=args.max_log_size)
    logging.basicConfig(level=args.log,
                        handlers=[
                            file_handler,
                            logging.StreamHandler()  # Also print to terminal.
                        ],
                        format='%(asctime)s [%(name)s] [%(levelname)s] %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p')
    # Websocket messages are too noisy, make sure they aren't higher than warning.
    logging.getLogger("websockets").setLevel(logging.WARNING)

    asyncio.run(main(args))
