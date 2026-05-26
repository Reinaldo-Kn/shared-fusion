from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

import os


def generate_launch_description():
    package_share = get_package_share_directory("human_interface")

    config_file = os.path.join(
        package_share,
        "config",
        "joystick_params.yaml",
    )

    return LaunchDescription(
        [
            Node(
                package="human_interface",
                executable="human_control_node",
                name="human_control_node",
                output="screen",
                parameters=[config_file],
            )
        ]
    )