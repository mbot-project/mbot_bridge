#ifndef MBOT_BRIDGE_ROBOT_H
#define MBOT_BRIDGE_ROBOT_H

#include <chrono>
#include <string>

#include <mbot_lcm_msgs/twist2D_t.hpp>
#include <mbot_lcm_msgs/pose2D_t.hpp>
#include <mbot_lcm_msgs/lidar_t.hpp>

#include "mbot_json_msgs.h"
#include "lcm_utils.h"
#include "comms.h"


class Robot
{
public:
    Robot(const std::string& hostname = "localhost", const int port = 5005)
    {
        uri_ = "ws://" + hostname + ":" + std::to_string(port);
    }

    void drive(const float vx, const float vy, const float wz) const;
    void stop() const;
    void resetOdometry() const;
    void readLidarScan(std::vector<float>& ranges, std::vector<float>& thetas) const;
    std::vector<float> readOdometry() const;
    std::vector<float> readSlamPose() const;

private:
    std::string uri_;

};

#endif // MBOT_BRIDGE_ROBOT_H
