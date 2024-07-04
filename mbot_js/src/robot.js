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
          console.warn("MBot API Error:", res.data);
        }
        else if (res.rtype !== MBotMessageType.RESPONSE) {
          // Check if an unknown error occured.
          console.warn("MBot API Error: Can't parse response:", res);
        }

        resolve(res);
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
        console.error('WebSocket error:', error);
        this.isConnecting = false;
        this.ws_subs[ch] = null;
        reject(error);
      };

      this.ws_subs[ch].onclose = () => {
        console.log('WebSocket connection closed');
        this.ws_subs[ch] = null;
      };
    });

    return promise;
  }

  unsubscribe(ch) {
    if (this.ws_subs[ch] === undefined || this.ws_subs[ch] === null) return Promise.resolve();

    if (this.ws_subs[ch].readyState === WebSocket.CONNECTING) {
      return Promise.reject(new Error('Cannot unsubscribe while connecting'));
    }

    return new Promise((resolve) => {
      if (this.ws_subs[ch].readyState === WebSocket.OPEN) {
        this.ws_subs[ch].onclose = () => {
          console.log('WebSocket connection closed');
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

  async readHostname(cb) {
    // Reads the hostname.
    let waitForData = this._read("HOSTNAME");
    waitForData.then((val) => {
      let hostname = "";
      if (val.rtype === MBotMessageType.RESPONSE) {
        hostname = val.data;
      }
      else {
        console.warn("Bad response:", val);
      }
      cb(hostname);
    });
    await waitForData;
  }

  async readChannels(cb) {
    // Gets the list of all channels subscribed to.
    let waitForData = this._read("CHANNELS");
    waitForData.then((val) => {
      let channels = [];
      if (val.rtype === MBotMessageType.RESPONSE) {
        channels = val.data;
      }
      else {
        console.warn("Bad response:", val);
      }
      cb(channels);
    });
    await waitForData;
  }

  drive(vx, vy, wz) {
    let data = { "vx": vx, "vy": vy, "wz": wz };
    this._publish(data, config.MOTOR_VEL_CMD.channel, config.MOTOR_VEL_CMD.dtype)
  }

  async readOdometry(odomCallback) {
    let waitForData = this._read(config.ODOMETRY.channel);
    waitForData.then((val) => {
      let odom = [];
      if (val.rtype === MBotMessageType.RESPONSE) {
        odom = [val.data.x, val.data.y, val.data.theta];
      }
      odomCallback(odom);
    });
    await waitForData;
  }
}

export { MBot };
