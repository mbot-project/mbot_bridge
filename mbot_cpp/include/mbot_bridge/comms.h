#ifndef MBOT_BRIDGE_WEBSOCKET_H
#define MBOT_BRIDGE_WEBSOCKET_H

#include <chrono>
#include <string>

#include <websocketpp/config/asio_no_tls_client.hpp>
#include <websocketpp/client.hpp>

#include "mbot_json_msgs.h"

using websocketpp::lib::placeholders::_1;
using websocketpp::lib::placeholders::_2;

typedef websocketpp::client<websocketpp::config::asio_client> WSClient;


class MBotWSCommBase
{
public:
    MBotWSCommBase(const std::string& uri = "ws://localhost:5005") :
        uri_(uri),
        failed_(false)
    {
        // Set logging to be pretty verbose (everything except message payloads)
        // c_.set_access_channels(websocketpp::log::alevel::all);
        // c_.clear_access_channels(websocketpp::log::alevel::frame_payload);
        // c_.set_error_channels(websocketpp::log::elevel::all);
        c_.clear_access_channels(websocketpp::log::alevel::all);
        c_.clear_error_channels(websocketpp::log::elevel::all);

        // m_endpoint.set_fail_handler(bind(&type::on_fail,this,::_1));
        c_.set_fail_handler(websocketpp::lib::bind(&MBotWSCommBase::on_fail, this, ::_1));

        // Initialize ASIO
        c_.init_asio();
    };

    int run()
    {
        failed_ = false;
        try {
            websocketpp::lib::error_code ec;
            WSClient::connection_ptr con = c_.get_connection(uri_, ec);
            if (ec) {
                std::cout << "[MBot API] ERROR: Could not create connection: " << ec.message() << std::endl;
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
    bool failed_;

    void on_fail(websocketpp::connection_hdl hdl)
    {
        std::cout << "[MBot API] WARNING: Connection to MBot Bridge failed." << std::endl;
        failed_ = true;
    }
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

    bool success() const
    {
        return res_type_ == MBotMessageType::RESPONSE && !failed_;
    };

    MBotMessageType getResponseType() const { return res_type_; }

private:
    std::string channel_;
    MBotMessageType res_type_;  // Response type, to check for errors.
    T data_;

    void on_open(websocketpp::connection_hdl hdl){
        // Request the data.
        MBotJSONMessage msg("", channel_, "", MBotMessageType::REQUEST);
        c_.send(hdl, msg.encode(), websocketpp::frame::opcode::text);
    }

    void on_message(websocketpp::connection_hdl hdl, WSClient::message_ptr msg) {
        MBotJSONMessage in_msg;
        in_msg.decode(msg->get_payload());
        res_type_ = in_msg.type();

        if (res_type_ == MBotMessageType::RESPONSE)
        {
            stringToLCMType(in_msg.data(), data_);
        }
        else if (res_type_ == MBotMessageType::ERROR)
        {
            std::cout << "[MBot API] WARNING: Read failed. " << in_msg.data() << std::endl;
        }
        else
        {
            std::cout << "[MBot API] WARNING: Read failed." << std::endl;
        }

        // Once we get the message back, we can stop listening.
        c_.close(hdl, websocketpp::close::status::normal, "");
    }
};

#endif // MBOT_BRIDGE_WEBSOCKET_H
