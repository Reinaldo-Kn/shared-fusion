# human-interface/joystick/examples/test_real_joystick.py

import time
import pygame

from joystick_interface import JoystickConfig, HumanControlInterface


def main():
    config = JoystickConfig(dt=0.05)
    controller = HumanControlInterface(config)

    pygame.init()
    pygame.joystick.init()

    joystick_count = pygame.joystick.get_count()

    if joystick_count == 0:
        print("No joystick detected.")
        print("Connect the joystick and try again.")
        return

    joystick = pygame.joystick.Joystick(0)
    joystick.init()

    print("Joystick detected:")
    print(f"  Name: {joystick.get_name()}")
    print(f"  Axes: {joystick.get_numaxes()}")
    print(f"  Buttons: {joystick.get_numbuttons()}")
    print()

    # Confirmed joystick mapping
    axis_lat = 0   # left/right: left negative, right positive
    axis_long = 3  # up/down: up negative, down positive

    print(f"Using axis_lat={axis_lat}, axis_long={axis_long}")
    print("Convention:")
    print("  joy_lat  < 0 -> left")
    print("  joy_lat  > 0 -> right")
    print("  joy_long < 0 -> ACCEL")
    print("  joy_long > 0 -> BRAKE")
    print("  joy_long = 0 -> COAST")
    print()
    print("Press CTRL+C to stop.")
    print()

    # Fake speed only for this Python test.
    # In ROS2, this will come from the real vehicle odometry/speed topic.
    current_speed = 0.0

    try:
        while True:
            loop_start = time.time()

            pygame.event.pump()

            joy_lat = joystick.get_axis(axis_lat)
            joy_long = joystick.get_axis(axis_long)

            output = controller.update(
                joy_lat=joy_lat,
                joy_long=joy_long,
                current_speed=current_speed,
            )

            # Fake vehicle speed update only for visualization.
            # This is not the real Zoe dynamics.
            current_speed += 0.02 * output.torque_setpoint * config.dt
            current_speed = max(0.0, current_speed)

            print(
                f"mode={output.active_mode:5s} | "
                f"joy_lat={joy_lat:+.3f} | "
                f"joy_long={joy_long:+.3f} | "
                f"steering={output.steering_setpoint:+.3f} rad | "
                f"v_ref={output.v_h_ref:+.3f} m/s | "
                f"brake={output.brake_h_cmd:+.1f} | "
                f"pi_torque={output.pi_torque_cmd:+.1f} Nm | "
                f"torque={output.torque_setpoint:+.1f} Nm | "
                f"fake_speed={current_speed:+.3f} m/s"
            )

            elapsed = time.time() - loop_start
            sleep_time = max(0.0, config.dt - elapsed)
            time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\nStopped by user.")

    finally:
        joystick.quit()
        pygame.quit()


if __name__ == "__main__":
    main()