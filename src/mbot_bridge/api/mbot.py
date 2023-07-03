import websockets
import asyncio
from mbot_bridge.utils.json_helpers import (
    MBotJSONRequest, MBotJSONPublish
)
from mbot_bridge.api import lcm_config


class Robot(object):
    """Utility class for controlling the robot."""

    def __init__(self, host="localhost", port=5000):
        self.uri = f"ws://{host}:{port}"

    """PUBLISHERS"""

    async def _send(self, ch, data, dtype):
        res = MBotJSONPublish(data, ch, dtype)
        async with websockets.connect(self.uri) as websocket:
            await websocket.send(res.encode())

    def drive(self, vx, vy, wz):
        data = {"vx": vx, "vy": vy, "wz": wz}
        asyncio.run(self._send(lcm_config.MOTOR_VEL_CMD.channel, data, lcm_config.MOTOR_VEL_CMD.dtype))

    """SUBSCRIBERS"""

    async def _request(self, ch):
        res = MBotJSONRequest(ch)
        async with websockets.connect(self.uri) as websocket:
            await websocket.send(res.encode())

            # Wait for the response
            response = await websocket.recv()

        return response

    def read_odometry(self):
        res = asyncio.run(self._request(lcm_config.ODOMETRY.channel))
        return res

    def read_slam_pose(self):
        pass

    def read_lidar(self):
        pass


if __name__ == '__main__':
    robot = Robot()
    robot.drive(0, 0, 0)
    odom = robot.read_odometry()
    print(odom)
