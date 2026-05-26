#!/usr/bin/env python3

# helpers/code/linux_joy_udp_receiver.py

import json
import socket

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy


class LinuxJoyUdpReceiver(Node):
    """
    Receives joystick data through UDP and publishes it as sensor_msgs/Joy.

    Intended development setup:

        Windows joystick + pygame
        -> UDP JSON
        -> this node on Linux/WSL
        -> /joy
    """

    def __init__(self):
        super().__init__("linux_joy_udp_receiver")

        self.declare_parameter("udp_ip", "172.27.151.229")
        self.declare_parameter("udp_port", 9999)
        self.declare_parameter("joy_topic", "/joy")
        self.declare_parameter("timer_period", 0.02)  # 50 Hz

        udp_ip = str(self.get_parameter("udp_ip").value)
        udp_port = int(self.get_parameter("udp_port").value)
        joy_topic = str(self.get_parameter("joy_topic").value)
        timer_period = float(self.get_parameter("timer_period").value)

        self.publisher = self.create_publisher(Joy, joy_topic, 10)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((udp_ip, udp_port))
        self.sock.setblocking(False)

        self.last_axes = []
        self.last_buttons = []

        self.timer = self.create_timer(timer_period, self.timer_callback)

        self.get_logger().info(
            f"Linux Joy UDP Receiver listening on {udp_ip}:{udp_port}"
        )
        self.get_logger().info(f"Publishing Joy messages to {joy_topic}")

    def timer_callback(self):
        try:
            while True:
                data, _ = self.sock.recvfrom(4096)
                payload = json.loads(data.decode("utf-8"))

                self.last_axes = [
                    float(value)
                    for value in payload.get("axes", [])
                ]

                self.last_buttons = [
                    int(value)
                    for value in payload.get("buttons", [])
                ]

        except BlockingIOError:
            pass

        except json.JSONDecodeError as exc:
            self.get_logger().warn(f"Invalid JSON received: {exc}")
            return

        if not self.last_axes:
            return

        msg = Joy()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.axes = self.last_axes
        msg.buttons = self.last_buttons

        self.publisher.publish(msg)

    def destroy_node(self):
        self.sock.close()
        super().destroy_node()


def main():
    rclpy.init()

    node = LinuxJoyUdpReceiver()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()