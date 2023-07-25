#include <mbot_bridge/robot.h>


int main(int argc, char* argv[])
{
    Robot robot;
    robot.drive(0, 0, 0);

    auto odom = robot.read_odometry();
    std::cout << "Odometry: ";
    for (auto& ele : odom) std::cout << ele << " ";
    std::cout << std::endl;

    robot.reset_odometry();
}
