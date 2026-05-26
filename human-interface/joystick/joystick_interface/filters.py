
class Saturation:
    """
    Equivalent to a Simulink Saturation block.
    """

    def __init__(self, min_value: float, max_value: float):
        if min_value > max_value:
            raise ValueError("min_value must be less than or equal to max_value")

        self.min_value = min_value
        self.max_value = max_value

    def apply(self, value: float) -> float:
        return float(max(self.min_value, min(self.max_value, value)))


class AsymmetricRateLimiter:
    """
    Equivalent to a Simulink Rate Limiter block with rising
    and falling slew rates.

    Example:
        rising_rate = 1.5
        falling_rate = -3.0
        dt = 0.05

        max positive variation per step = 1.5 * 0.05 = 0.075
        max negative variation per step = -3.0 * 0.05 = -0.150
    """

    def __init__(
        self,
        rising_rate: float,
        falling_rate: float,
        dt: float,
        initial_value: float = 0.0,
    ):
        if dt <= 0.0:
            raise ValueError("dt must be positive")

        if rising_rate < 0.0:
            raise ValueError("rising_rate must be positive or zero")

        if falling_rate > 0.0:
            raise ValueError("falling_rate must be negative or zero")

        self.rising_rate = rising_rate
        self.falling_rate = falling_rate
        self.dt = dt
        self.previous_value = initial_value

    def apply(self, value: float) -> float:
        delta = value - self.previous_value

        max_delta = self.rising_rate * self.dt
        min_delta = self.falling_rate * self.dt

        if delta > max_delta:
            delta = max_delta
        elif delta < min_delta:
            delta = min_delta

        self.previous_value += delta
        return float(self.previous_value)

    def reset(self, value: float = 0.0) -> None:
        self.previous_value = value


class FirstOrderTransferFunction:
    """
    Discrete approximation of a first-order transfer function:

        G(s) = K / (tau*s + 1)
    """

    def __init__(
        self,
        gain: float,
        tau: float,
        dt: float,
        initial_value: float = 0.0,
    ):
        if dt <= 0.0:
            raise ValueError("dt must be positive")

        if tau <= 0.0:
            raise ValueError("tau must be positive")

        self.gain = gain
        self.tau = tau
        self.dt = dt
        self.y = initial_value

        self.alpha = dt / (tau + dt)

    def update(self, u: float) -> float:
        self.y = self.y + self.alpha * (self.gain * u - self.y)
        return float(self.y)

    def reset(self, value: float = 0.0) -> None:
        self.y = value