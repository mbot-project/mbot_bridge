import websockets
import asyncio
from mbot_bridge.utils.type_utils import dict_to_lcm_type
from mbot_bridge.utils.json_messages import (
    MBotJSONRequest, MBotJSONPublish, MBotJSONMessage, MBotMessageType
)
from mbot_bridge.api.lcm_config import LCMConfig


class Robot(object):
    """Utility class for controlling the robot."""

    def __init__(self, host="localhost", port=5000):
        self.uri = f"ws://{host}:{port}"
        self.lcm_config = LCMConfig()

    """PUBLISHERS"""

    async def _send(self, ch, data, dtype):
        res = MBotJSONPublish(data, ch, dtype)
        async with websockets.connect(self.uri) as websocket:
            await websocket.send(res.encode())

    def drive(self, vx, vy, wz):
        data = {"vx": vx, "vy": vy, "wz": wz}
        asyncio.run(self._send(self.lcm_config.MOTOR_VEL_CMD.channel, data, self.lcm_config.MOTOR_VEL_CMD.dtype))

    def stop(self):
        self.drive(0, 0, 0)

    """SUBSCRIBERS"""

    async def _request(self, ch):
        res = MBotJSONRequest(ch)
        async with websockets.connect(self.uri) as websocket:
            await websocket.send(res.encode())

            # Wait for the response
            response = await websocket.recv()

        # Convert this to a JSON message.
        response = MBotJSONMessage(response, from_json=True)

        # Check if this is an error. If so, print it and quit.
        if response.type() == MBotMessageType.ERROR:
            print("ERROR:", response.data())
            return

        # If this was a response as expected, convert it to an LCM message and return.
        if response.type() == MBotMessageType.RESPONSE:
            msg = dict_to_lcm_type(response.data(), response.dtype())
            return msg
        else:
            print("ERROR: Got a bad response type:", response.encode())

    def read_odometry(self):
        res = asyncio.run(self._request(self.lcm_config.ODOMETRY.channel))
        return res

    def read_slam_pose(self):
        res = asyncio.run(self._request(self.lcm_config.SLAM_POSE.channel))
        return res

    def read_lidar(self):
        res = asyncio.run(self._request(self.lcm_config.LIDAR.channel))
        return res


if __name__ == '__main__':
    robot = Robot()
    robot.drive(0, 0, 0)
    odom = robot.read_odometry()
    print(odom)
