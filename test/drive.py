import time
from mbot_bridge.api.mbot import Robot

# Initialize a robot object.
robot = Robot()

# Drive in a square.
robot.drive(0.5, 0, 0)
time.sleep(1)
robot.drive(0, 0.5, 0)
time.sleep(1)
robot.drive(-0.5, 0, 0)
time.sleep(1)
robot.drive(0, -0.5, 0)
time.sleep(1)

# Make sure motors are stopped.
robot.stop()
