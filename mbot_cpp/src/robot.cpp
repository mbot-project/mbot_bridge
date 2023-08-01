#include <mbot_bridge/comms.h>
#include <mbot_bridge/robot.h>

#include <mbot_lcm_msgs/twist2D_t.hpp>
#include <mbot_lcm_msgs/pose2D_t.hpp>
#include <mbot_lcm_msgs/lidar_t.hpp>


void Robot::drive(const float vx, const float vy, const float wz) const
{
    mbot_lcm_msgs::twist2D_t msg;
    msg.vx = vx;
    msg.vy = vy;
    msg.wz = wz;

    MBotBridgePublisher<mbot_lcm_msgs::twist2D_t> pub(MBOT_VEL_CMD_CHANNEL, msg, MBOT_VEL_CMD_TYPE, uri_);
    pub.run();
}

void Robot::stop() const
{
    drive(0, 0, 0);
}

void Robot::resetOdometry() const
{
    mbot_lcm_msgs::pose2D_t msg;
    msg.x = 0;
    msg.y = 0;
    msg.theta = 0;

    MBotBridgePublisher<mbot_lcm_msgs::pose2D_t> pub(ODOMETRY_RESET_CHANNEL, msg, ODOMETRY_RESET_TYPE, uri_);
    pub.run();
}

void Robot::readLidarScan(std::vector<float>& ranges, std::vector<float>& thetas) const
{
    // Empty the vectors.
    ranges.clear();
    thetas.clear();

    MBotBridgeReader<mbot_lcm_msgs::lidar_t> reader(LIDAR_CHANNEL);
    reader.run();

    // Only populate the lidar vectors if the read was successful.
    if (reader.success())
    {
        mbot_lcm_msgs::lidar_t data = reader.getData();
        ranges = data.ranges;
        thetas = data.thetas;
    }
}

std::vector<float> Robot::readOdometry() const
{
    MBotBridgeReader<mbot_lcm_msgs::pose2D_t> reader(ODOMETRY_CHANNEL);
    reader.run();

    std::vector<float> odom;
    // Only populate the odometry vector if the read was successful.
    if (reader.success())
    {
        mbot_lcm_msgs::pose2D_t data = reader.getData();
        odom = {data.x, data.y, data.theta};
    }

    return odom;
}

std::vector<float> Robot::readSlamPose() const
{
    MBotBridgeReader<mbot_lcm_msgs::pose2D_t> reader(SLAM_POSE_CHANNEL);
    reader.run();

    std::vector<float> pose;
    // Only populate the odometry vector if the read was successful.
    if (reader.success())
    {
        mbot_lcm_msgs::pose2D_t data = reader.getData();
        pose = {data.x, data.y, data.theta};
    }

    return pose;
}