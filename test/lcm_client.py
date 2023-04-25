import lcm
import time
from mbot_lcm_msgs import omni_motor_command_t

_lcm = lcm.LCM("udpm://239.255.76.67:7667?ttl=1")

cmd = omni_motor_command_t()
cmd.vx = 0
cmd.vy = 0
cmd.wz = 0
for i in range(10):
    print(f"PUB:  vx: {cmd.vx} vy: {cmd.vy} wz: {cmd.wz}")
    _lcm.publish("TEST_CMD", cmd.encode())
    time.sleep(2)
    cmd.vx += 1
