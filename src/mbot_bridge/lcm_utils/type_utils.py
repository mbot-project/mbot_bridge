from mbot_lcm_msgs import omni_motor_command_t

LCM_TYPES = {
    "omni_motor_command_t": omni_motor_command_t
}


def decode(data, type_name):
    """Decode raw data from LCM channel to type based on type string."""
    if type_name not in LCM_TYPES:
        raise Exception("LCM Type {type_name} is not supported.")

    return LCM_TYPES[type_name].decode(data)


def lcm_type_to_dict(data):
    """LCM types, once decoded"""
    data_d = {att: getattr(data, att) for att in data.__slots__}
    return data_d
