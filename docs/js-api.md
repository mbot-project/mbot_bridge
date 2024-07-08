# MBot Bridge API: Javascript

The Javascript API can be used either with Node.JS or in plain Javascript.

## Installation

### Node.JS (Recommended)

To use the MBot API in a Node project, clone this repo then do:
```bash
cd mbot_bridge/mbot_js
npm install
npm link
```
The command `npm link` makes a symlink of this package available to link in other packages. This is an alternative to registering this package as an official NPM package.

Then, in your own Node project, do:
```bash
cd my_project/
npm link mbot-js-api
```

To create a MBot object in your project, do:
```javascript
import { MBot } from "mbot-js-api";

const mbot = new MBot(mbotIP);
```
where `mbotIP` is the IP address of the mbot.

**Tip:** The IP of the robot is often the one you type into the browser to access the web app hosted on the robot. To get this IP, do:
```javascript
const mbotIP = window.location.host.split(":")[0]  // Grab the IP from which this page was accessed.
```

### Plain Javascript

#### Method 1: Use Latest Release (Recommended)

*TODO:* Add instructions to link to the latest release (when it is released).

#### Method 2: Build from source

Use this method if you are developing or if you need the latest (unreleased) version.

First, clone this repo, then do:
```bash
cd mbot_bridge/mbot_js
npm install
npm run build
```
Then include the bundled script `mbot_js/dist/main.js` in your HTML.

To create a MBot object, do:
```javascript
const mbot = new MBotAPI.MBot(mbotIP);
```
where `mbotIP` is the IP address of the mbot.

## Usage

The Javascript API is based off of [*promises*](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise), which are objects built for handling asynchronous tasks.

*Coming soon*
