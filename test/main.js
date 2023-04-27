window.addEventListener("DOMContentLoaded", () => {
  console.log("Hello!", window.location.host)
  const websocket = new WebSocket("ws://localhost:5000/");

  websocket.onopen = (event) => {
    // websocket.send("Connected!");
    let conn_data = {type: "init", data: "connected"};
    websocket.send(JSON.stringify(conn_data));

    // let request_data = {type: "request", channel: "SLAM_POSE"};
    let request_data = {type: "publish", channel: "MBOT_MOTOR_COMMAND",
                        dtype: "twist2D_t", data: {vx: 1, vy: -1, wz: 0.1}};
    websocket.send(JSON.stringify(request_data));
  };

  websocket.onmessage = (event) => {
    console.log("Recieved:", event.data);
    websocket.send("Thanks for the data");
  };
});
