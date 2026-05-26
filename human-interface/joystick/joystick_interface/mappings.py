
def clamp(value: float, min_value: float, max_value: float) -> float:
    """
    Saturates a value between min_value and max_value.

    Equivalent to a Simulink Saturation block.
    """
    return float(max(min_value, min(max_value, value)))


def clamp_joystick(value: float, joy_min: float = -1.0, joy_max: float = 1.0) -> float:
    """
    Ensures joystick input stays inside the expected range [-1, 1].
    """
    return clamp(value, joy_min, joy_max)


def cubic_mapping(value: float) -> float:
    """
    Equivalent to the Simulink u^3 block.

    This makes the command smoother around zero while preserving
    the full command at the extremes.

    Examples:
        0.5  ->  0.125
       -0.5  -> -0.125
        1.0  ->  1.0
       -1.0  -> -1.0
    """
    return float(value ** 3)


def acceleration_mapping(joy_long: float) -> float:
    """
    Maps joy_long to the acceleration branch input.

    Based on the Simulink model:

        joy_long -> gain -1 -> saturation [0, 1]

    Therefore:
        joy_long = -1 -> 1.0 acceleration command
        joy_long =  0 -> 0.0
        joy_long =  1 -> 0.0
    """
    acc = -joy_long
    return clamp(acc, 0.0, 1.0)


def brake_mapping(joy_long: float) -> float:
    """
    Maps joy_long to the brake branch input.

    Based on the Simulink model:

        joy_long -> saturation [0, 1]

    Therefore:
        joy_long = -1 -> 0.0
        joy_long =  0 -> 0.0
        joy_long =  1 -> 1.0 brake command
    """
    return clamp(joy_long, 0.0, 1.0)