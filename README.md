# MBot Bridge

Server and API to bridge robot functionality with student code.

Dependencies:
* Python 3 (tested on 3.10)
* LCM 1.4+ (tested on 1.5)
* MBot messages for Python

## Install Instructions

```bash
pip install -r requirements.txt
pip install -e .
```

## Usage

To run the server, do:
```bash
python -m mbot_bridge.server [--config [PATH/TO/CONFIG]]
```
The `--config` argument is optional and will default to `src/mbot_bridge/config/default.yml`.

## C++ API

To use the C++ API, first install the websocket library at the latest release version:
```bash
git clone git@github.com:zaphoyd/websocketpp.git
cd websocketpp
git checkout 0.8.2
mkdir build && cd build
cmake ..
make
sudo make install
```
Then, compile this code in the root of this directory:
```bash
mkdir build && cd build
cmake ..
make
```
A test script is available at:
```bash
./mbot_cpp/mbot_cpp_test
```
