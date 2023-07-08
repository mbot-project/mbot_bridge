import json


class MBotMessageType(object):
    INIT = 99
    REQUEST = 0
    PUBLISH = 1
    RESPONSE = 2
    ERROR = -98
    INVALID = -99


class BadMBotRequestError(Exception):
    pass


class MBotJSONMessage(object):
    def __init__(self, data=None, channel=None, dtype=None, rtype=None, from_json=False):
        if from_json:
            self.decode(data)
        else:
            if rtype not in [MBotMessageType.INIT, MBotMessageType.REQUEST,
                             MBotMessageType.PUBLISH, MBotMessageType.RESPONSE,
                             MBotMessageType.ERROR, MBotMessageType.INVALID]:
                raise AttributeError(f"Invalid message type: {rtype}")
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
        if self._request_type == MBotMessageType.INIT:
            rtype = "init"
        elif self._request_type == MBotMessageType.PUBLISH:
            rtype = "publish"
        elif self._request_type == MBotMessageType.REQUEST:
            rtype = "request"
        elif self._request_type == MBotMessageType.RESPONSE:
            rtype = "response"
        elif self._request_type == MBotMessageType.ERROR:
            rtype = "error"
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
            request_type = MBotMessageType.REQUEST
        elif request_type == "publish":
            request_type = MBotMessageType.PUBLISH
        elif request_type == "response":
            request_type = MBotMessageType.RESPONSE
        elif request_type == "error":
            request_type = MBotMessageType.ERROR
        elif request_type == "init":
            request_type = MBotMessageType.INIT
        else:
            request_type = MBotMessageType.INVALID
            raise BadMBotRequestError(f"Invalid request type: \"{request_type}\"")

        # The request should have a channel if it is a publish or a request type.
        channel = None
        if request_type == MBotMessageType.REQUEST or request_type == MBotMessageType.PUBLISH:
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
        if request_type == MBotMessageType.PUBLISH and (msg_data is None or dtype is None):
            raise BadMBotRequestError("Publish was requested but data or data type is missing.")

        self._channel = channel
        self._data = msg_data
        self._dtype = dtype
        self._request_type = request_type


class MBotJSONRequest(MBotJSONMessage):
    def __init__(self, channel, dtype=None):
        super().__init__(channel=channel, dtype=dtype, rtype=MBotMessageType.REQUEST)


class MBotJSONResponse(MBotJSONMessage):
    def __init__(self, data, channel, dtype):
        super().__init__(data, channel=channel, dtype=dtype, rtype=MBotMessageType.RESPONSE)


class MBotJSONPublish(MBotJSONMessage):
    def __init__(self, data, channel, dtype):
        super().__init__(data, channel=channel, dtype=dtype, rtype=MBotMessageType.PUBLISH)


class MBotJSONError(MBotJSONMessage):
    def __init__(self, msg):
        super().__init__(msg, rtype=MBotMessageType.ERROR)