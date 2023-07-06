#ifndef MBOT_BRIDGE_ROBOT_H
#define MBOT_BRIDGE_ROBOT_H

#include <chrono>
#include <string>

#include <mbot_lcm_msgs/twist2D_t.hpp>
#include <mbot_lcm_msgs/pose2D_t.hpp>

#include <websocketpp/config/asio_no_tls_client.hpp>
#include <websocketpp/client.hpp>

#include "mbot_json_msgs.h"
#include "lcm_utils.h"

using websocketpp::lib::placeholders::_1;
using websocketpp::lib::placeholders::_2;

typedef websocketpp::client<websocketpp::config::asio_client> WSClient;


/**
 * Gets the current time in microseconds.
 */
static inline int getTimeMicro()
{
    auto now = std::chrono::system_clock::now();
    return now.time_since_epoch().count();
}


class MBotWSCommBase
{
public:
    MBotWSCommBase(const std::string& uri = "ws://localhost:5005") :
        uri_(uri)
    {
        // Set logging to be pretty verbose (everything except message payloads)
        c_.set_access_channels(websocketpp::log::alevel::all);
        c_.clear_access_channels(websocketpp::log::alevel::frame_payload);
        c_.set_error_channels(websocketpp::log::elevel::all);

        // Initialize ASIO
        c_.init_asio();
    };

    int run()
    {
        try {
            websocketpp::lib::error_code ec;
            WSClient::connection_ptr con = c_.get_connection(uri_, ec);
            if (ec) {
                std::cout << "ERROR: Could not create connection: " << ec.message() << std::endl;
                return -1;
            }

            // Note that connect here only requests a connection. No network messages are
            // exchanged until the event loop starts running in the next line.
            c_.connect(con);

            // Start the ASIO io_service run loop
            // this will cause a single connection to be made to the server. c.run()
            // will exit when this connection is closed.
            c_.run();
        } catch (websocketpp::exception const & e) {
            std::cout << e.what() << std::endl;
            return -1;
        }
        return 0;
    }

protected:
    WSClient c_;
    std::string uri_;
};


template <class T>
class MBotBridgePublisher : public MBotWSCommBase
{
public:
    MBotBridgePublisher(const std::string& ch, const T& data, const std::string& dtype,
                        const std::string& uri = "ws://localhost:5005") :
        MBotWSCommBase(uri),
        channel_(ch),
        dtype_(dtype),
        data_(data)
    {
        // Register the open handler.
        c_.set_open_handler(websocketpp::lib::bind(&MBotBridgePublisher::on_open, this, ::_1));
    };

private:
    std::string channel_, dtype_;
    T data_;

    void on_open(websocketpp::connection_hdl hdl){
        MBotJSONMessage msg(lcmTypeToString(data_), channel_, dtype_, MBotMessageType::PUBLISH);
        std::cout << "Connection open! Sending: " << msg.encode() << std::endl;
        c_.send(hdl, msg.encode(), websocketpp::frame::opcode::text);

        // Once the message is published, we don't need to wait for a message in response.
        c_.close(hdl, websocketpp::close::status::normal, "");
    }
};


template <class T>
class MBotBridgeReader : public MBotWSCommBase
{
public:
    MBotBridgeReader(const std::string& ch, const std::string& uri = "ws://localhost:5005") :
        MBotWSCommBase(uri),
        channel_(ch)
    {
        // Register the open handler.
        c_.set_open_handler(websocketpp::lib::bind(&MBotBridgeReader::on_open, this, ::_1));
        c_.set_message_handler(websocketpp::lib::bind(&MBotBridgeReader::on_message, this, ::_1, ::_2));
    };

    T getData() const
    {
        return data_;
    }

    MBotMessageType getResponseType() const { return res_type_; }

private:
    std::string channel_;
    MBotMessageType res_type_;  // Response type, to check for errors.
    T data_;

    void on_open(websocketpp::connection_hdl hdl){
        std::cout << "Open" << std::endl;

        // Request the data.
        MBotJSONMessage msg("", channel_, "", MBotMessageType::REQUEST);
        c_.send(hdl, msg.encode(), websocketpp::frame::opcode::text);
    }

    void on_message(websocketpp::connection_hdl hdl, WSClient::message_ptr msg) {
        std::cout << "Message received: " << msg->get_payload() << std::endl;
        MBotJSONMessage in_msg;
        in_msg.decode(msg->get_payload());
        data_ = stringToLCMType(in_msg.data());
        res_type_ = in_msg.type();

        // Once we get the message back, we can stop listening.
        c_.close(hdl, websocketpp::close::status::normal, "");
    }
};


class Robot
{
public:
    Robot(const std::string& hostname = "localhost", const int port = 5005)
    {
        uri_ = "ws://" + hostname + ":" + std::to_string(port);
    }

    void drive(const float vx, const float vy, const float wz) const
    {
        mbot_lcm_msgs::twist2D_t msg;
        msg.vx = vx;
        msg.vy = vy;
        msg.wz = wz;

        MBotBridgePublisher<mbot_lcm_msgs::twist2D_t> pub(MBOT_VEL_CMD_CHANNEL, msg, MBOT_VEL_CMD_TYPE, uri_);
        pub.run();
    }

    std::vector<float> read_odometry() const
    {
        MBotBridgeReader<mbot_lcm_msgs::pose2D_t> reader(ODOMETRY_CHANNEL);
        reader.run();
        mbot_lcm_msgs::pose2D_t data = reader.getData();

        std::vector<float> odom = {data.x, data.y, data.theta};
        return odom;
    }

private:
    std::string uri_;

};

#endif // MBOT_BRIDGE_ROBOT_H
