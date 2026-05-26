# joystick_interface/human_intention.py
from dataclasses import dataclass

from .config import JoystickConfig
from .filters import Saturation, AsymmetricRateLimiter
from .mappings import (
    clamp_joystick,
    cubic_mapping,
    acceleration_mapping,
    brake_mapping,
)


@dataclass
class HumanJoystickOutput:
    """
    Output of the human joystick mapping block.

    steering_h_ref:
        Human steering reference [rad].

    v_h_ref:
        Human desired longitudinal speed [m/s].

    brake_h_cmd:
        Human braking command.
        Negative value means braking.
    """

    steering_h_ref: float
    v_h_ref: float
    brake_h_cmd: float


class HumanJoystickInterface:
    """
    Python implementation of the Simulink joystick mapping.

    Simulink equivalent:

        joy_lat
        -> u^3
        -> rate limiter
        -> gain -2*pi
        -> saturation
        -> steering_h_ref

        joy_long
        -> gain -1
        -> saturation [0, 1]
        -> u^3
        -> gain 6
        -> rate limiter
        -> saturation
        -> v_h_ref

        joy_long
        -> saturation [0, 1]
        -> u^3
        -> gain -400
        -> rate limiter
        -> saturation
        -> brake_h_cmd
    """

    def __init__(self, config: JoystickConfig | None = None):
        self.config = config or JoystickConfig()

        # Lateral rate limiter:
        # Applied after cubic mapping and before steering gain.
        self.steering_rate_limiter = AsymmetricRateLimiter(
            rising_rate=self.config.steering_rate_rising,
            falling_rate=self.config.steering_rate_falling,
            dt=self.config.dt,
        )

        self.steering_saturation = Saturation(
            min_value=self.config.steering_min,
            max_value=self.config.steering_max,
        )

        # Longitudinal speed reference rate limiter.
        self.speed_rate_limiter = AsymmetricRateLimiter(
            rising_rate=self.config.speed_rate_rising,
            falling_rate=self.config.speed_rate_falling,
            dt=self.config.dt,
        )

        self.speed_saturation = Saturation(
            min_value=self.config.speed_min,
            max_value=self.config.speed_max,
        )

        # Brake command rate limiter.
        self.brake_rate_limiter = AsymmetricRateLimiter(
            rising_rate=self.config.brake_rate_rising,
            falling_rate=self.config.brake_rate_falling,
            dt=self.config.dt,
        )

        self.brake_saturation = Saturation(
            min_value=self.config.brake_min,
            max_value=self.config.brake_max,
        )

    def update(self, joy_lat: float, joy_long: float) -> HumanJoystickOutput:
        """
        Computes human reference commands from joystick axes.
        """

        joy_lat = clamp_joystick(
            joy_lat,
            joy_min=self.config.joy_min,
            joy_max=self.config.joy_max,
        )

        joy_long = clamp_joystick(
            joy_long,
            joy_min=self.config.joy_min,
            joy_max=self.config.joy_max,
        )

        steering_h_ref = self._compute_steering_reference(joy_lat)
        v_h_ref = self._compute_speed_reference(joy_long)
        brake_h_cmd = self._compute_brake_command(joy_long)

        return HumanJoystickOutput(
            steering_h_ref=steering_h_ref,
            v_h_ref=v_h_ref,
            brake_h_cmd=brake_h_cmd,
        )

    def _compute_steering_reference(self, joy_lat: float) -> float:
        # joy_lat -> u^3
        steering_signal = cubic_mapping(joy_lat)

        # rate limiter before the gain
        steering_signal = self.steering_rate_limiter.apply(steering_signal)

        # gain -2*pi
        steering_h_ref = self.config.steering_gain * steering_signal

        # final saturation
        steering_h_ref = self.steering_saturation.apply(steering_h_ref)

        return steering_h_ref

    def _compute_speed_reference(self, joy_long: float) -> float:
        # joy_long -> gain -1 -> saturation [0, 1]
        acc_signal = acceleration_mapping(joy_long)

        # u^3
        acc_signal = cubic_mapping(acc_signal)

        # gain 6
        v_h_ref = self.config.max_human_speed * acc_signal

        # rate limiter
        v_h_ref = self.speed_rate_limiter.apply(v_h_ref)

        # final saturation
        v_h_ref = self.speed_saturation.apply(v_h_ref)

        return v_h_ref

    def _compute_brake_command(self, joy_long: float) -> float:
        # joy_long -> saturation [0, 1]
        brake_signal = brake_mapping(joy_long)

        # u^3
        brake_signal = cubic_mapping(brake_signal)

        # gain -400
        brake_h_cmd = self.config.brake_gain * brake_signal

        # rate limiter
        brake_h_cmd = self.brake_rate_limiter.apply(brake_h_cmd)

        # final saturation
        brake_h_cmd = self.brake_saturation.apply(brake_h_cmd)

        return brake_h_cmd

    def reset(self) -> None:
        """
        Resets all internal states
        """
        self.steering_rate_limiter.reset(0.0)
        self.speed_rate_limiter.reset(0.0)
        self.brake_rate_limiter.reset(0.0)