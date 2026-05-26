from dataclasses import dataclass

from .config import JoystickConfig
from .human_intention import HumanJoystickInterface, HumanJoystickOutput
from .longitudinal_control import LongitudinalController, LongitudinalControlOutput


@dataclass
class HumanControlOutput:
    """
    Final output of the human control interface
    """

    # Final commands to vehicle
    steering_setpoint: float
    torque_setpoint: float

    # Intermediate human references
    v_h_ref: float
    brake_h_cmd: float

    # Debug/control information
    pi_torque_cmd: float
    speed_error: float
    active_mode: str


class HumanControlInterface:
    """
    Full human control interface.

    This class combines:

        1. HumanJoystickInterface:
            joy_lat, joy_long
            -> steering_h_ref, v_h_ref, brake_h_cmd

        2. LongitudinalController:
            v_h_ref, current_speed, brake_h_cmd
            -> torque_setpoint
    """

    def __init__(self, config: JoystickConfig | None = None):
        self.config = config or JoystickConfig()

        self.joystick = HumanJoystickInterface(self.config)
        self.longitudinal_controller = LongitudinalController(self.config)

    def update(
        self,
        joy_lat: float,
        joy_long: float,
        current_speed: float,
    ) -> HumanControlOutput:
        """
        Computes steering and torque commands from joystick and speed.

        Args:
            joy_lat:
                Lateral joystick axis in [-1, 1].

            joy_long:
                Longitudinal joystick axis in [-1, 1].
                Based on the current convention:
                    joy_long < 0 -> acceleration
                    joy_long > 0 -> braking

            current_speed:
                Measured vehicle speed [m/s].

        Returns:
            HumanControlOutput with final vehicle commands.
        """

        joystick_output: HumanJoystickOutput = self.joystick.update(
            joy_lat=joy_lat,
            joy_long=joy_long,
        )

        longitudinal_output: LongitudinalControlOutput = (
            self.longitudinal_controller.update(
                v_h_ref=joystick_output.v_h_ref,
                current_speed=current_speed,
                brake_h_cmd=joystick_output.brake_h_cmd,
                joy_long=joy_long,
            )
        )

        return HumanControlOutput(
            steering_setpoint=joystick_output.steering_h_ref,
            torque_setpoint=longitudinal_output.torque_setpoint,
            v_h_ref=joystick_output.v_h_ref,
            brake_h_cmd=joystick_output.brake_h_cmd,
            pi_torque_cmd=longitudinal_output.pi_torque_cmd,
            speed_error=longitudinal_output.speed_error,
            active_mode=longitudinal_output.active_mode,
        )

    def reset(self) -> None:
        """
        Resets all internal states
        """
        self.joystick.reset()
        self.longitudinal_controller.reset()