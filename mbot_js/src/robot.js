import { MBotMessageType, MBotJSONMessage } from "./mbot_json_msgs.js";
import config from "./lcm_config.js";

/**
 * MBot class provides methods to interact with the MBot Bridge Server via WebSocket.
 * It supports publishing messages, subscribing to channels, and reading data from channels.
 */

class MBot {
  /**
   * Constructs an instance of the MBot class.
   *
   * @param {string} [hostname="localhost"] - The hostname of the MBot Bridge Server.
   * @param {number} [port=5005] - The port of the MBot Bridge Server.
   */
  constructor(hostname = "localhost", port = 5005) {
    this.address = "ws://" + hostname + ":" + port;
    this.ws_subs = {};
  }

  /**
   * Private method to send a data request to a specified channel and receive the response.
   *
   * @param {string} ch - The channel to read data from.
   * @returns {Promise} - A Promise that resolves with the received data or rejects if there is an error.
   * @private
   */
  _read(ch) {
    let msg = new MBotJSONMessage(null, ch, null, MBotMessageType.REQUEST);

    let promise = new Promise((resolve, reject) => {
      const websocket = new WebSocket(this.address);

      websocket.onopen = (event) => {
        websocket.send(msg.encode());
      };

      websocket.onmessage = (event) => {
        let res = new MBotJSONMessage()
        res.decode(event.data);
        websocket.close();

        // Check for error from the server.
        if (res.rtype === MBotMessageType.ERROR) {
          reject("MBot API Error: " + res.data + " on channel: " + ch);
        }
        else if (res.rtype !== MBotMessageType.RESPONSE) {
          // Check if an unknown error occured.
          reject("MBot API Error: Can't parse response on channel: " + ch);
        }
        resolve(res);
      };

      websocket.onerror = (event) => {
        reject("MBot API Error: MBot Bridge Server connection error.");
      };
    });

    return promise;
  }

  /**
   * Publishes data to a specified channel.
   *
   * @param {string} data - The data to be published. Must be JSON-encodable.
   * @param {string} ch - The channel to publish the data to.
   * @param {string} dtype - The data type of the published data.
   */
  publish(data, ch, dtype) {
    let msg = new MBotJSONMessage(data, ch, dtype, MBotMessageType.PUBLISH);
    const websocket = new WebSocket(this.address);

    websocket.onopen = (event) => {
      websocket.send(msg.encode());
      websocket.close();
    };

    websocket.onerror = (event) => {
      console.error("MBot API Error: MBot Bridge Server connection error.");
    };
  }

  /**
   * Subscribes to a specified channel and binds a callback function to handle incoming messages.
   *
   * @param {string} ch - The channel to subscribe to.
   * @param {function} cb - The callback function to handle incoming messages from the specified channel.
   * @returns {Promise} - A Promise that resolves when the connection to the MBot Bridge is successfully opened and the
   *                      subscription message is sent. It rejects if there is an error in establishing the connection
   *                      or sending the subscription message.
   */
  subscribe(ch, cb) {
    let msg = new MBotJSONMessage(null, ch, null, MBotMessageType.SUBSCRIBE);
    if (this.ws_subs[ch]) {
      return Promise.resolve();
    }

    let promise = new Promise((resolve, reject) => {
      this.ws_subs[ch] = new WebSocket(this.address);

      this.ws_subs[ch].onopen = (event) => {
        this.ws_subs[ch].send(msg.encode());
        resolve();
      };

      this.ws_subs[ch].onmessage = (event) => {
        let res = new MBotJSONMessage();
        res.decode(event.data);
        cb(res);
      };

      this.ws_subs[ch].onerror = (error) => {
        this.ws_subs[ch] = null;
        reject("MBot API Error: Cannot subscribe to channel " + ch);
      };

      this.ws_subs[ch].onclose = () => {
        this.ws_subs[ch] = null;
      };
    });

    return promise;
  }

  /**
   * Unsubscribes from a specified channel.
   *
   * @param {string} ch - The channel to unsubscribe from.
   * @returns {Promise} - A Promise that resolves when the connection to the given channel is closed or immediately if
   *                      no subscription exists. It rejects if trying to unsubscribe while connecting.
   */
  unsubscribe(ch) {
    // No subscription exists so no action is needed.
    if (this.ws_subs[ch] === undefined || this.ws_subs[ch] === null) return Promise.resolve();

    if (this.ws_subs[ch].readyState === WebSocket.CONNECTING) {
      return Promise.reject(new Error('Cannot unsubscribe while connecting'));
    }

    return new Promise((resolve) => {
      if (this.ws_subs[ch].readyState === WebSocket.OPEN) {
        this.ws_subs[ch].onclose = () => {
          this.ws_subs[ch] = null;
          resolve();
        };

        this.ws_subs[ch].close();
      }
      else {
        this.ws_subs[ch] = null;
        resolve();
      }
    });
  }

  /*******************
   * READING HELPERS *
   *******************/

  /**
   * Reads the latest data from a specified channel.
   *
   * @param {string} ch - The channel to read data from.
   * @returns {Promise<*>} - A Promise that resolves with the latest data from the specified channel.
   */
  readData(ch) {
    let promise = new Promise((resolve, reject) => {
      this._read(ch).then((val) => {
        resolve(val.data);
      }).catch((error) => {
        reject(error);
      });
    });

    return promise;
  }

  /**
   * Reads the robot's hostname.
   *
   * @returns {Promise<string>} - A Promise that resolves with the robot's hostname.
   */
  readHostname() {
    return this.readData("HOSTNAME");
  }

  /**
   * Gets the list of all channels subscribed to.
   *
   * @returns {Promise<array>} - A Promise that resolves with an array of all subscribed channels.
   */
  readChannels() {
    return this.readData("CHANNELS");
  }

  /**
   * Reads the robot's odometry data.
   *
   * @returns {Promise<array>} - A Promise that resolves with an array [x, y, theta] representing the odometry data.
   */
  readOdometry() {
    let promise = new Promise((resolve, reject) => {
      this._read(config.ODOMETRY.channel).then((val) => {
        const odom = [val.data.x, val.data.y, val.data.theta];
        resolve(odom)
      }).catch((error) => {
        reject(error)
      });
    });

    return promise;
  }

  /*******************
   * PUBLISH HELPERS *
   *******************/

  /**
   * Sends drive commands to the robot.
   *
   * @param {number} vx - The linear velocity in the x direction.
   * @param {number} vy - The linear velocity in the y direction.
   * @param {number} wz - The angular velocity around the z axis.
   */
  drive(vx, vy, wz) {
    let data = { "vx": vx, "vy": vy, "wz": wz };
    this.publish(data, config.MOTOR_VEL_CMD.channel, config.MOTOR_VEL_CMD.dtype)
  }
}

export { MBot, config };
