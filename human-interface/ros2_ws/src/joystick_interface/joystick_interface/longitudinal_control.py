from dataclasses import dataclass

from .config import JoystickConfig
from .filters import Saturation, AsymmetricRateLimiter


@dataclass
class LongitudinalControlOutput:
    """
    Output of the longitudinal control block.

    torque_setpoint:
        Final torque command to be sent to the vehicle [Nm].

    pi_torque_cmd:
        Torque command generated only by the PI controller [Nm].

    brake_h_cmd:
        Brake command coming from the joystick mapping.

    speed_error:
        Difference between desired speed and measured speed [m/s].
    """

    torque_setpoint: float
    pi_torque_cmd: float
    brake_h_cmd: float
    speed_error: float
    active_mode: str


class PIController:
    """
    Discrete PI controller.

    Continuous form:
        u(t) = Kp * e(t) + Ki * integral(e(t) dt)

    Discrete approximation:
        integral[k] = integral[k-1] + e[k] * dt
        u[k] = Kp * e[k] + Ki * integral[k]
    """

    def __init__(
        self,
        kp: float,
        ki: float,
        dt: float,
        integral_min: float,
        integral_max: float,
    ):
        if dt <= 0.0:
            raise ValueError("dt must be positive")

        if integral_min > integral_max:
            raise ValueError("integral_min must be less than or equal to integral_max")

        self.kp = kp
        self.ki = ki
        self.dt = dt
        self.integral_min = integral_min
        self.integral_max = integral_max
        self.integral = 0.0

    def update(self, error: float) -> float:
        self.integral += error * self.dt

        # Anti-windup by clamping the integral state
        self.integral = max(
            self.integral_min,
            min(self.integral_max, self.integral),
        )

        output = self.kp * error + self.ki * self.integral
        return float(output)

    def reset(self) -> None:
        self.integral = 0.0


class LongitudinalController:
    """
    Converts human desired speed into a vehicle torque setpoint.

    Inputs:
        v_h_ref:
            Human desired speed [m/s].

        current_speed:
            Measured vehicle speed [m/s].

        brake_h_cmd:
            Human brake command. Negative values mean braking.

    Output:
        torque_setpoint:
            Final command to be sent to /torque_setpoint.
    """

    def __init__(self, config: JoystickConfig | None = None):
        self.config = config or JoystickConfig()

        self.pi = PIController(
            kp=self.config.kp,
            ki=self.config.ki,
            dt=self.config.dt,
            integral_min=self.config.integral_min,
            integral_max=self.config.integral_max,
        )

        self.torque_saturation = Saturation(
            min_value=self.config.torque_min,
            max_value=self.config.torque_max,
        )

        self.torque_rate_limiter = AsymmetricRateLimiter(
            rising_rate=self.config.torque_rate_rising,
            falling_rate=self.config.torque_rate_falling,
            dt=self.config.dt,
        )


    #
    def update(
        self,
        v_h_ref: float,
        current_speed: float,
        brake_h_cmd: float = 0.0,
        joy_long: float = 0.0,
    ) -> LongitudinalControlOutput:
        speed_error = v_h_ref - current_speed
        active_mode = self._get_active_mode(joy_long)

        if active_mode == "COAST":
            self.pi.reset()

            torque_setpoint = self.config.coast_torque
            torque_setpoint = self.torque_saturation.apply(torque_setpoint)

            self.torque_rate_limiter.reset(torque_setpoint)

            return LongitudinalControlOutput(
                torque_setpoint=torque_setpoint,
                pi_torque_cmd=0.0,
                brake_h_cmd=brake_h_cmd,
                speed_error=speed_error,
                active_mode=active_mode,
            )

        if active_mode == "BRAKE" and self.config.use_brake_override:
            self.pi.reset()

            torque_setpoint = self.torque_saturation.apply(brake_h_cmd)
            self.torque_rate_limiter.reset(torque_setpoint)

            return LongitudinalControlOutput(
                torque_setpoint=torque_setpoint,
                pi_torque_cmd=0.0,
                brake_h_cmd=brake_h_cmd,
                speed_error=speed_error,
                active_mode=active_mode,
            )

        # ============================================================
        # ACCEL mode
        # ============================================================
        
        pi_torque_cmd = self.pi.update(speed_error) * self.config.torque_gain
        pi_torque_cmd = max(0.0, pi_torque_cmd)
        torque_setpoint = self.torque_rate_limiter.apply(pi_torque_cmd)
        torque_setpoint = self.torque_saturation.apply(torque_setpoint)

        return LongitudinalControlOutput(
            torque_setpoint=torque_setpoint,
            pi_torque_cmd=pi_torque_cmd,
            brake_h_cmd=brake_h_cmd,
            speed_error=speed_error,
            active_mode=active_mode,
        )

    def _get_active_mode(self, joy_long: float) -> str:
        if joy_long < -self.config.coast_threshold:
            return "ACCEL"

        if joy_long > self.config.coast_threshold:
            return "BRAKE"

        return "COAST"

    def reset(self) -> None:
        self.pi.reset()
        self.torque_rate_limiter.reset(0.0)