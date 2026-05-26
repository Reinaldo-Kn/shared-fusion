# Human Interface with Joystick for Shared Control

This repository contains code for a human interface that uses a PS3 joystick to provide control of a vehicle.

## Building Zoe CAN Drivers and Interface
First make sure to have the zoe can drivers and interface set up. For this part, the codes should be acesseable from UTC GitLab, under the name `can_zoe` and `can_interface`. Once you have `git clone` those repositories, make sure to place them in the same ROS2 workspace as this repository, so that the directory structure looks like this:

```
ros2_ws/
├── can_interface/
├── can_zoe/
├── human-interface/
├── joystick_interface/
```

Then, you can build the ROS2 workspace using colcon:
```bash
colcon build --symlink-install --packages-select can_interface can_zoe
```
To test if the build was successful, you can source the workspace and run the `can_zoe_interface` node:
```bash
source install/setup.bash
ros2 interface list | grep can_zoe_interfaces
# or ros2 interface show can_zoe_interfaces/msg/Kinematics
```
It should output
```bash
    can_zoe_interfaces/msg/FlashingLights
    can_zoe_interfaces/msg/Kinematics
    can_zoe_interfaces/msg/Torques
    can_zoe_interfaces/msg/VehicleState
    can_zoe_interfaces/msg/WheelSpeeds
    can_zoe_interfaces/msg/WheelTops
```
---

## Building and Running the Joystick Interface
First build both the `joystick_interface` and `human_interface` packages using colcon:

```bash
colcon build --symlink-install --packages-select joystick_interface human_interface
```
Then, source the workspace and run the joystick interface node:
```bash
source install/setup.bash
ros2 launch human_interface human_control.launch.py
```
If you run
```bash
ros2 param get /human_control_node torque_max
```
it should output
```bash
Double value is: 30.0
```
That is the maximum torque defined in `joystick_params.yaml` that the joystick interface will command to the vehicle. You can change this value and re-run the node to see how it affects the joystick control.

---

## Running the Vehicle Interface

After the workspace has been built successfully, source the ROS2 workspace and launch the human interface node:

```bash
cd human-interface/ros2_ws
source install/setup.bash
ros2 launch human_interface human_control.launch.py
```

The node subscribes to `/joy` and `/vehicle/kinematics`, computes the human steering and torque commands, and publishes them to:

- `/steering_angle_setpoint`
- `/torque_setpoint`

To inspect the published commands, run in separate terminals:

```bash
source install/setup.bash
ros2 topic echo /steering_angle_setpoint
```

```bash
source install/setup.bash
ros2 topic echo /torque_setpoint
```

You can also check that the parameters were loaded correctly:

```bash
ros2 param get /human_control_node steering_topic
ros2 param get /human_control_node torque_topic
ros2 param get /human_control_node torque_max
```


---
## Working on Windows
The hole project is developed with Linux in mind, but it is possible to work on Windows as well. Use WSL with ROS2 Humble or Jazzy installed. For the joystick, use `helpers/code/windows_joy_udp_sender.py` with the proper IP address of the WSL (`hostname -I` in WSL terminal). On the WSL side, run `helpers/code/linux_joy_udp_receiver.py` to receive the joystick data and publish it as ROS2 messages at `/joy` topic.