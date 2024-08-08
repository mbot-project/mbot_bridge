import { MBotMessageType, MBotJSONMessage } from "./mbot_json_msgs.js";
import config from "./lcm_config.js";


class MBot {
  constructor(hostname = "localhost", port = 5005) {
    this.address = "ws://" + hostname + ":" + port;
    this.ws_subs = {};
  }

  async _read(ch) {
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

  _publish(data, ch, dtype) {
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
        reject("MBot API Error: Cannot subscribe to channel "+ channel);
      };

      this.ws_subs[ch].onclose = () => {
        this.ws_subs[ch] = null;
      };
    });

    return promise;
  }

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

  readHostname() {
    let promise = new Promise((resolve, reject) => {
      this._read("HOSTNAME").then((val) => {
        resolve(val.data)
      }).catch((error) => {
        reject(error)
      });
    });

    return promise;
  }

  readChannels() {
    // Gets the list of all channels subscribed to.
    let promise = new Promise((resolve, reject) => {
      this._read("CHANNELS").then((val) => {
        resolve(val.data)
      }).catch((error) => {
        reject(error)
      });
    });

    return promise;
  }

  drive(vx, vy, wz) {
    let data = { "vx": vx, "vy": vy, "wz": wz };
    this._publish(data, config.MOTOR_VEL_CMD.channel, config.MOTOR_VEL_CMD.dtype)
  }

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
}

export { MBot, config };
