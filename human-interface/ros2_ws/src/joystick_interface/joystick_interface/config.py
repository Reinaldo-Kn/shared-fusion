from dataclasses import dataclass
import math


from dataclasses import dataclass
import math


@dataclass
class JoystickConfig:
    """
    Configuration parameters for the human joystick interface.

    This file centralizes the parameters used by the Python implementation
    of the Simulink joystick model
    """

    # ============================================================
    # General
    # ============================================================

    # Sampling time [s]
    # 0.05 s = 20 Hz
    dt: float = 0.05

    # ============================================================
    # Joystick input convention
    # ============================================================

    # Expected joystick input range:
    # joy_lat  in [-1, 1]
    # joy_long in [-1, 1]
    #
    # Based on Simulink model:
    # joy_long < 0 -> acceleration / desired speed
    # joy_long > 0 -> braking

    joy_min: float = -1.0
    joy_max: float = 1.0

    # ============================================================
    # Lateral mapping
    # ============================================================

    # Simulink:
    # joy_lat -> u^3 -> rate limiter -> gain -2*pi -> saturation
    steering_gain: float = -2.0 * math.pi

    # Rate limiter applied after cubic mapping and before steering gain
    # Units: normalized joystick command per second
    steering_rate_rising: float = 1.5
    steering_rate_falling: float = -1.5

    # Final steering saturation [rad]
    steering_min: float = -2.0 * math.pi
    steering_max: float = 2.0 * math.pi

    # ============================================================
    # Longitudinal speed reference mapping
    # ============================================================

    # Simulink:
    # joy_long -> gain -1 -> saturation [0,1] -> cubic -> gain 6
    # -> rate limiter -> saturation
    max_human_speed: float = 6.0  # [m/s]

    # Rate limiter for v_h_ref
    # Rising: acceleration of desired speed
    # Falling: reduction of desired speed
    # Units: m/s²
    speed_rate_rising: float = 1.5
    speed_rate_falling: float = -3.0

    # Final speed reference saturation [m/s]
    speed_min: float = 0.0
    speed_max: float = 6.0

    # ============================================================
    # Brake command mapping
    # ============================================================

    # Simulink:
    # joy_long -> saturation [0,1] -> cubic -> gain -400
    # -> rate limiter -> saturation
    brake_gain: float = -400.0

    # Rate limiter for brake command
    # Units: brake command units per second
    brake_rate_rising: float = 800.0
    brake_rate_falling: float = -800.0

    # Final brake command saturation
    brake_min: float = -400.0
    brake_max: float = 0.0

    # ============================================================
    # Free wheel behavior 
    # ============================================================
    
    # around zero joystick input
    coast_threshold: float = 0.02
    coast_torque: float = 0.0
    # ============================================================
    # Longitudinal PI controller
    # ============================================================

    # PI gains calculated from MATLAB
    kp: float = 51.385331
    ki: float = 9.224695

    # Anti-windup limits for the integral term
    integral_min: float = -1.0
    integral_max: float = 1.0

    # ============================================================
    # Torque command limits
    # ============================================================

    # Zoe torque logic:
    # -1000 -> hard braking
    # -400  -> starts braking
    # 0     -> free wheel
    # 50    -> strong acceleration
    torque_min: float = -1000.0
    torque_max: float = 50.0

    # Since kp and ki are already in a realistic torque scale,
    torque_gain: float = 1.0

    # Optional rate limiter for final torque command
    # Units: Nm/s
    torque_rate_rising: float = 800.0
    torque_rate_falling: float = -800.0

    # When brake_h_cmd is active, it can override the PI torque command.
    use_brake_override: bool = True