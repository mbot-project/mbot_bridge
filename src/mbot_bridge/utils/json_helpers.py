import json


class MBotRequestType(object):
    INIT = 99
    REQUEST = 0
    PUBLISH = 1
    INVALID = -99


class BadMBotRequestError(Exception):
    pass


class MBotJSONRequest(object):
    """Message parser for incoming requests."""

    def __init__(self, data):
        self._raw_data = data
        # First try to load the data as JSON.
        try:
            data = json.loads(data)
        except json.decoder.JSONDecodeError:
            raise BadMBotRequestError(f"Message is not valid JSON: \"{self._raw_data}\"")

        # Get the type and channel for the request.
        try:
            request_type = data["type"]
        except KeyError:
            raise BadMBotRequestError("JSON request does not have a type attribute.")

        # Parse the type.
        if request_type == "request":
            self._request_type = MBotRequestType.REQUEST
        elif request_type == "publish":
            self._request_type = MBotRequestType.PUBLISH
        elif request_type == "init":
            self._request_type = MBotRequestType.INIT
        else:
            self._request_type = MBotRequestType.INVALID
            raise BadMBotRequestError(f"Invalid request type: \"{request_type}\"")

        # The request should have a channel if it is a publish or a request type.
        self._channel = None
        if self._request_type == MBotRequestType.REQUEST or self._request_type == MBotRequestType.PUBLISH:
            try:
                self._channel = data["channel"]
            except KeyError:
                raise BadMBotRequestError("JSON request does not have a channel attribute.")

        # Read the data, if any.
        self.data, self.dtype = None, None
        if "data" in data:
            self.data = data["data"]
        if "dtype" in data:
            self.dtype = data["dtype"]

        # If this was a publish request, data is required.
        if self._request_type == MBotRequestType.PUBLISH and (self.data is None or self.dtype is None):
            raise BadMBotRequestError("Publish was requested but data or data type is missing.")

    def type(self):
        return self._request_type

    def channel(self):
        return self._channel


class MBotJSONResponse(object):
    def __init__(self, channel, data, dtype):
        self.channel = channel
        self.data = data
        self.dtype = dtype

    def as_json(self):
        data = {"type": "response", "channel": self.channel,
                "dtype": self.dtype, "data": self.data}
        return json.dumps(data)


class MBotJSONError(object):
    def __init__(self, msg="", data=None):
        self.message = msg
        self.data = data

    def as_json(self):
        data = {"type": "error", "msg": self.message}
        if self.data is not None:
            data.update({"data": self.data})
        return json.dumps(data)
