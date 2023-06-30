import websockets
import asyncio
from mbot_bridge.utils.json_helpers import (
    MBotJSONRequest, MBotJSONResponse, MBotJSONError,
    MBotRequestType, BadMBotRequestError
)


class Robot(object):
    """Utility class for controlling the robot."""

    def __init__(self):
        self.uri = "ws://localhost:5000"

    """PUBLISHERS"""

    async def _send(self, ch, data, dtype):
        res = MBotJSONRequest(ch, data, dtype, "publish")
        async with websockets.connect(self.uri) as websocket:
            await websocket.send(res.encode())

    def drive(self, vx, vy, wz):
        data = {"vx": vx, "vy": vy, "wz": wz}
        asyncio.run(self._send("MBOT_VEL_CMD", data, "twist2D_t"))

    """SUBSCRIBERS"""

    async def _request(self, ch):
        res = MBotJSONRequest(ch, rtype="request")
        async with websockets.connect(self.uri) as websocket:
            await websocket.send(res.encode())

            # Wait for the response
            response = await websocket.recv()

        return response

    def read_odometry(self):
        res = asyncio.run(self._request("ODOMETRY"))
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
