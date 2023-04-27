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
        setattr(lcm_msg, k, v)

    return lcm_msg
