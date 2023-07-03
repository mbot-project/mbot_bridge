import json


class MBotRequestType(object):
    INIT = 99
    REQUEST = 0
    PUBLISH = 1
    RESPONSE = 2
    INVALID = -99


class BadMBotRequestError(Exception):
    pass


class MBotJSONMessage(object):
    def __init__(self, data=None, channel=None, dtype=None, rtype=None, from_json=False):
        if from_json:
            self.decode(data)
        else:
            if rtype not in [MBotRequestType.INIT, MBotRequestType.REQUEST,
                             MBotRequestType.PUBLISH, MBotRequestType.RESPONSE,
                             MBotRequestType.INVALID]:
                raise Exception(f"Invalid message type: {rtype}")
            self._request_type = rtype
            self._data = data
            self._channel = channel
            self._dtype = dtype

    def data(self):
        return self._data

    def dtype(self):
        return self._dtype

    def type(self):
        return self._request_type

    def channel(self):
        return self._channel

    def encode(self):
        if self._request_type == MBotRequestType.INIT:
            rtype = "init"
        elif self._request_type == MBotRequestType.PUBLISH:
            rtype = "publish"
        elif self._request_type == MBotRequestType.REQUEST:
            rtype = "request"
        elif self._request_type == MBotRequestType.RESPONSE:
            rtype = "response"
        else:
            rtype = "invalid"

        msg = {"type": rtype}

        if self._channel is not None:
            msg.update({"channel": self._channel})
        if self._dtype is not None:
            msg.update({"dtype": self._dtype})
        if self._data is not None:
            msg.update({"data": self._data})

        return json.dumps(msg)

    def decode(self, data):
        raw_data = data
        # First try to load the data as JSON.
        try:
            data = json.loads(data)
        except json.decoder.JSONDecodeError:
            raise BadMBotRequestError(f"Message is not valid JSON: \"{raw_data}\"")

        # Get the type and channel for the request.
        try:
            request_type = data["type"]
        except KeyError:
            raise BadMBotRequestError("JSON request does not have a type attribute.")

        # Parse the type.
        if request_type == "request":
            request_type = MBotRequestType.REQUEST
        elif request_type == "publish":
            request_type = MBotRequestType.PUBLISH
        elif request_type == "response":
            request_type = MBotRequestType.RESPONSE
        elif request_type == "init":
            request_type = MBotRequestType.INIT
        else:
            request_type = MBotRequestType.INVALID
            raise BadMBotRequestError(f"Invalid request type: \"{request_type}\"")

        # The request should have a channel if it is a publish or a request type.
        channel = None
        if request_type == MBotRequestType.REQUEST or request_type == MBotRequestType.PUBLISH:
            try:
                channel = data["channel"]
            except KeyError:
                raise BadMBotRequestError("JSON request does not have a channel attribute.")

        # Read the data, if any.
        msg_data, dtype = None, None
        if "data" in data:
            msg_data = data["data"]
        if "dtype" in data:
            dtype = data["dtype"]

        # If this was a publish request, data is required.
        if request_type == MBotRequestType.PUBLISH and (msg_data is None or dtype is None):
            raise BadMBotRequestError("Publish was requested but data or data type is missing.")

        self._channel = channel
        self._data = msg_data
        self._dtype = dtype
        self._request_type = request_type


class MBotJSONRequest(MBotJSONMessage):
    def __init__(self, channel, dtype=None):
        super().__init__(channel=channel, dtype=dtype, rtype=MBotRequestType.REQUEST)


class MBotJSONResponse(MBotJSONMessage):
    def __init__(self, data, channel, dtype):
        super().__init__(data, channel=channel, dtype=dtype, rtype=MBotRequestType.RESPONSE)


class MBotJSONPublish(MBotJSONMessage):
    def __init__(self, data, channel, dtype):
        super().__init__(data, channel=channel, dtype=dtype, rtype=MBotRequestType.PUBLISH)


class MBotJSONError(object):
    def __init__(self, msg="", data=None):
        self.message = msg
        self.data = data

    def encode(self):
        data = {"type": "error", "msg": self.message}
        if self.data is not None:
            data.update({"data": self.data})
        return json.dumps(data)
