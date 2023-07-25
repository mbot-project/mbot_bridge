#ifndef MBOT_BRIDGE_LCM_UTILS_H
#define MBOT_BRIDGE_LCM_UTILS_H

#include <string>
#include <sstream>

#include <mbot_lcm_msgs/twist2D_t.hpp>
#include <mbot_lcm_msgs/pose2D_t.hpp>

#include "json_utils.h"

// Subs.
#define ODOMETRY_CHANNEL "MBOT_ODOMETRY"
#define SLAM_POSE_CHANNEL "SLAM_POSE"
#define SLAM_MAP_CHANNEL "SLAM_MAP"
#define LIDAR_CHANNEL "LIDAR"
// Pubs.
#define ODOMETRY_RESET_CHANNEL "MBOT_ODOMETRY_RESET"
#define ODOMETRY_RESET_TYPE "pose2D_t"
#define MBOT_VEL_CMD_CHANNEL "MBOT_VEL_CMD"
#define MBOT_VEL_CMD_TYPE "twist2D_t"
#define CONTROLLER_PATH_CHANNEL "CONTROLLER_PATH"
#define CONTROLLER_PATH_TYPE "path2D_t"


static inline std::string lcmTypeToString(const mbot_lcm_msgs::twist2D_t& data)
{
    std::ostringstream oss;
    oss << keyValToJSON("vx", data.vx) << ",";
    oss << keyValToJSON("vy", data.vy) << ",";
    oss << keyValToJSON("wz", data.wz);
    return oss.str();
}


static inline std::string lcmTypeToString(const mbot_lcm_msgs::pose2D_t& data)
{
    std::ostringstream oss;
    oss << keyValToJSON("x", data.x) << ",";
    oss << keyValToJSON("y", data.y) << ",";
    oss << keyValToJSON("theta", data.theta);
    return oss.str();
}


static inline mbot_lcm_msgs::pose2D_t stringToLCMType(const std::string& data)
{
    mbot_lcm_msgs::pose2D_t p;
    if (data.find("x") != std::string::npos)
    {
        auto x = strip(fetch(data, "x"));
        if (x.length() > 0) p.x = std::stof(x);
    }
    if (data.find("y") != std::string::npos)
    {
        auto y = strip(fetch(data, "y"));
        if (y.length() > 0) p.y = std::stof(y);
    }
    if (data.find("theta") != std::string::npos)
    {
        auto theta = strip(fetch(data, "theta"));
        if (theta.length() > 0) p.theta = std::stof(theta);
    }
    if (data.find("utime") != std::string::npos)
    {
        auto utime = fetch(data, "utime");
        if (utime.length() > 0) p.utime = std::stol(utime);
    }
    return p;
}


#endif // MBOT_BRIDGE_LCM_UTILS_H
