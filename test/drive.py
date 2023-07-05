import time
from mbot_bridge.api import Robot

# Initialize a robot object.
robot = Robot()

# Read the latest odometry message.
odom = robot.read_odometry()
print("Odometry:", odom)

# Read the latest lidar scan.
ranges, thetas = robot.read_lidar()
print("Ranges length:", len(ranges), "Thetas length:", len(thetas))

# Drive in a square.
vel = 0.5
robot.drive(vel, 0, 0)
time.sleep(1)
robot.drive(0, vel, 0)
time.sleep(1)
robot.drive(-vel, 0, 0)
time.sleep(1)
robot.drive(0, -vel, 0)
time.sleep(1)

# Make sure motors are stopped.
robot.stop()
