import math

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Joy
from std_msgs.msg import Float64

from can_zoe_interfaces.msg import Kinematics, VehicleState

from joystick_interface import JoystickConfig, HumanControlInterface


class HumanControlNode(Node):
    def __init__(self):
        super().__init__("human_control_node")

        # ============================================================
        # Parameters
        # ============================================================

        self.declare_parameter("dt", 0.05)

        # Joystick axes
        self.declare_parameter("axis_lat", 0)
        self.declare_parameter("axis_long", 3)

        # Input topics
        self.declare_parameter("joy_topic", "/joy")
        self.declare_parameter("kinematics_topic", "/vehicle/kinematics")
        self.declare_parameter("vehicle_state_topic", "/vehicle/vehicle_state")

        # Output topics
        self.declare_parameter("steering_topic", "/steering_angle_setpoint")
        self.declare_parameter("torque_topic", "/torque_setpoint")

        # Human desired speed
        self.declare_parameter("max_human_speed", 6.0)

        # PI controller
        self.declare_parameter("kp", 51.385331)
        self.declare_parameter("ki", 9.224695)

        # Mode logic
        self.declare_parameter("coast_threshold", 0.02)

        # Lateral control
        self.declare_parameter("steering_gain", -2.0 * math.pi)
        self.declare_parameter("steering_rate_rising", 1.5)
        self.declare_parameter("steering_rate_falling", -1.5)

        # Longitudinal reference rate limiter
        self.declare_parameter("speed_rate_rising", 1.5)
        self.declare_parameter("speed_rate_falling", -3.0)

        # Brake control
        self.declare_parameter("brake_gain", -400.0)
        self.declare_parameter("brake_rate_rising", 800.0)
        self.declare_parameter("brake_rate_falling", -800.0)

        # Torque limits
        self.declare_parameter("torque_min", -1000.0)
        self.declare_parameter("torque_max", 30.0)

        # Safety options

        self.declare_parameter("block_positive_torque_with_parking_brake", True)

        # Logging
        self.declare_parameter("log_every_n_callbacks", 5)

        # ============================================================
        # Read parameters
        # ============================================================

        self.dt = float(self.get_parameter("dt").value)

        self.axis_lat = int(self.get_parameter("axis_lat").value)
        self.axis_long = int(self.get_parameter("axis_long").value)

        joy_topic = str(self.get_parameter("joy_topic").value)
        kinematics_topic = str(self.get_parameter("kinematics_topic").value)
        vehicle_state_topic = str(self.get_parameter("vehicle_state_topic").value)

        steering_topic = str(self.get_parameter("steering_topic").value)
        torque_topic = str(self.get_parameter("torque_topic").value)


        self.block_positive_torque_with_parking_brake = bool(
            self.get_parameter("block_positive_torque_with_parking_brake").value
        )

        self.log_every_n_callbacks = int(
            self.get_parameter("log_every_n_callbacks").value
        )

        # ============================================================
        # Controller configuration
        # ============================================================

        config = JoystickConfig(
            dt=self.dt,
            max_human_speed=float(self.get_parameter("max_human_speed").value),
            kp=float(self.get_parameter("kp").value),
            ki=float(self.get_parameter("ki").value),
            coast_threshold=float(self.get_parameter("coast_threshold").value),
            steering_gain=float(self.get_parameter("steering_gain").value),
            steering_rate_rising=float(self.get_parameter("steering_rate_rising").value),
            steering_rate_falling=float(self.get_parameter("steering_rate_falling").value),
            speed_rate_rising=float(self.get_parameter("speed_rate_rising").value),
            speed_rate_falling=float(self.get_parameter("speed_rate_falling").value),
            brake_gain=float(self.get_parameter("brake_gain").value),
            brake_rate_rising=float(self.get_parameter("brake_rate_rising").value),
            brake_rate_falling=float(self.get_parameter("brake_rate_falling").value),
            torque_min=float(self.get_parameter("torque_min").value),
            torque_max=float(self.get_parameter("torque_max").value),
        )

        self.controller = HumanControlInterface(config)

        # ============================================================
        # Internal state
        # ============================================================

        self.current_speed = 0.0
        self.has_kinematics = False

        self.has_vehicle_state = False
        self.start = False
        self.drive = False
        self.parking_brake = False

        self.callback_count = 0

        # ============================================================
        # Subscribers
        # ============================================================

        self.create_subscription(
            Joy,
            joy_topic,
            self.joy_callback,
            10,
        )

        self.create_subscription(
            Kinematics,
            kinematics_topic,
            self.kinematics_callback,
            10,
        )

        self.create_subscription(
            VehicleState,
            vehicle_state_topic,
            self.vehicle_state_callback,
            10,
        )

        # ============================================================
        # Publishers
        # ============================================================

        self.steering_pub = self.create_publisher(
            Float64,
            steering_topic,
            10,
        )

        self.torque_pub = self.create_publisher(
            Float64,
            torque_topic,
            10,
        )

        self.get_logger().info("Human control node started.")
        self.get_logger().info(f"joy_topic: {joy_topic}")
        self.get_logger().info(f"kinematics_topic: {kinematics_topic}")
        self.get_logger().info(f"vehicle_state_topic: {vehicle_state_topic}")
        self.get_logger().info(f"steering_topic: {steering_topic}")
        self.get_logger().info(f"torque_topic: {torque_topic}")
        self.get_logger().info(f"axis_lat={self.axis_lat}, axis_long={self.axis_long}")

    def kinematics_callback(self, msg: Kinematics):
        self.current_speed = float(msg.longitudinal_speed)
        self.has_kinematics = True

    def vehicle_state_callback(self, msg: VehicleState):
        self.start = bool(msg.start)
        self.drive = bool(msg.drive)
        self.parking_brake = bool(msg.parking_brake)
        self.has_vehicle_state = True

    def joy_callback(self, msg: Joy):
        if len(msg.axes) <= max(self.axis_lat, self.axis_long):
            self.get_logger().warn(
                f"Joy message has {len(msg.axes)} axes, "
                f"but axis_lat={self.axis_lat}, axis_long={self.axis_long}"
            )
            return

        joy_lat = float(msg.axes[self.axis_lat])
        joy_long = float(msg.axes[self.axis_long])

        output = self.controller.update(
            joy_lat=joy_lat,
            joy_long=joy_long,
            current_speed=self.current_speed,
        )

        steering_value = float(output.steering_setpoint)
        torque_value = float(output.torque_setpoint)

        # ============================================================
        # Safety layer
        # ============================================================

        if (
            self.block_positive_torque_with_parking_brake
            and self.has_vehicle_state
            and self.parking_brake
            and torque_value > 0.0
        ):
            self.get_logger().warn(
                "Parking brake is active. Blocking positive torque."
            )
            torque_value = 0.0

        # ============================================================
        # Publish commands
        # ============================================================

        steering_msg = Float64()
        steering_msg.data = steering_value

        torque_msg = Float64()
        torque_msg.data = torque_value

        self.steering_pub.publish(steering_msg)
        self.torque_pub.publish(torque_msg)

        # ============================================================
        # Logging
        # ============================================================

        self.callback_count += 1

        if self.callback_count % self.log_every_n_callbacks == 0:
            self.get_logger().info(
                f"mode={output.active_mode:5s} | "
                f"joy_lat={joy_lat:+.3f} | "
                f"joy_long={joy_long:+.3f} | "
                f"speed={self.current_speed:+.3f} m/s | "
                f"has_kinematics={self.has_kinematics} | "
                f"v_ref={output.v_h_ref:+.3f} m/s | "
                f"steering={steering_value:+.3f} rad | "
                f"brake={output.brake_h_cmd:+.1f} | "
                f"pi_torque={output.pi_torque_cmd:+.1f} Nm | "
                f"torque={torque_value:+.1f} Nm | "
                f"start={self.start} | "
                f"drive={self.drive} | "
                f"parking_brake={self.parking_brake}"
            )


def main(args=None):
    rclpy.init(args=args)

    node = HumanControlNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()