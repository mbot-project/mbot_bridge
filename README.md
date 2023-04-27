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
