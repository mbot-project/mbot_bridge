window.addEventListener("DOMContentLoaded", () => {
  console.log("Hello!", window.location.host)
  const robot = new MBotAPI.Robot("10.0.0.66");
  robot.drive(0, 0, 0);
  robot.readOdometry((odom) => {console.log("Odom:", odom);});

  let sub = false;
  document.getElementById('subscribeButton').addEventListener('click', function() {
    if (!sub) {
      robot.subscribe(config.ODOMETRY.channel, (odom) => { console.log("SUB:", odom); });
      sub = true;
    }
    else {
      robot.unsubscribe(config.ODOMETRY.channel);
      sub = false;
    }
  });
});
