#include <mbot_bridge/robot.h>


int main(int argc, char* argv[])
{
    Robot robot;
    robot.drive(0, 0, 0);

    auto odom = robot.readOdometry();
    std::cout << "Odometry: ";
    for (auto& ele : odom) std::cout << ele << " ";
    std::cout << std::endl;

    auto pose = robot.readSlamPose();
    std::cout << "SLAM pose: ";
    for (auto& ele : pose) std::cout << ele << " ";
    std::cout << std::endl;

    std::vector<float> ranges, thetas;
    robot.readLidarScan(ranges, thetas);
    std::cout << "Lidar scan length: " << ranges.size() << " " << thetas.size() << std::endl;

    robot.resetOdometry();

}
