from setuptools import find_packages, setup
from glob import glob
import os

package_name = 'human_interface'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join("share", package_name, "launch"), glob("launch/*.launch.py")),
        (os.path.join("share", package_name, "config"), glob("config/*.yaml")),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='reinaldo kn',
    maintainer_email='reinaldo.kaminski-neto@etu.utc.fr',
    description='ROS2 human joystick interface for shared control experiments',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            "human_control_node = human_interface.human_control_node:main",
        ],
    },
)
