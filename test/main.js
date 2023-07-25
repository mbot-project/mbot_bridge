window.addEventListener("DOMContentLoaded", () => {
  console.log("Hello!");
  const robotIP = window.location.host.split(":")[0]  // Grab the IP from which this page was accessed.
  const robot = new MBotAPI.Robot(robotIP);
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
