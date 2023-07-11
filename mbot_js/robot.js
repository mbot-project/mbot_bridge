
class Robot {
  constructor(hostname="localhost", port=5005) {
    this.address = "ws://" + hostname + ":" + port;
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

  drive(vx, vy, wz) {
    let data = {"vx": vx, "vy": vy, "wz": wz};
    this._publish(data, config.MOTOR_VEL_CMD.channel, config.MOTOR_VEL_CMD.dtype)
  }

  async readOdometry(odomCallback) {
    let waitForData = this._read(config.ODOMETRY.channel);
    waitForData.then((val) => {
      let odom = [];
      if (val.rtype === MBotMessageType.RESPONSE)
      {
        odom = [val.data.x, val.data.y, val.data.theta];
      }
      odomCallback(odom);
    });
    await waitForData;
  }
}
