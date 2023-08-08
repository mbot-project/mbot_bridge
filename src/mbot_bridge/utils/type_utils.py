import mbot_lcm_msgs


def str_to_lcm_type(dtype):
    """Accesses the message type by string. Raises AttributeError if the class type is invalid."""
    return getattr(mbot_lcm_msgs, dtype)


def decode(data, dtype):
    """Decode raw data from LCM channel to type based on type string."""
    lcm_obj = str_to_lcm_type(dtype)
    return lcm_obj.decode(data)


def lcm_type_to_dict(data):
    """LCM types, once decoded"""
    data_d = {att: getattr(data, att) for att in data.__slots__}
    return data_d


def dict_to_lcm_type(data, dtype):
    lcm_msg = str_to_lcm_type(dtype)()

    for k, v in data.items():
        # If one of the values is a list, we must check for types that need to be converted recursively.
        if isinstance(v, list):
            val_dtype = lcm_msg.__typenames__[lcm_msg.__slots__.index(k)]
            if val_dtype.startswith("mbot_lcm_msgs"):
                val_dtype = val_dtype.replace("mbot_lcm_msgs.", "")
                # Recursively convert to the correct data type.
                v = [dict_to_lcm_type(val, val_dtype) for val in v]

        setattr(lcm_msg, k, v)

    return lcm_msg
