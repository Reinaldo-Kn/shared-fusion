# human-interface/joystick/examples/check_trigger_analog.py

import time
import pygame


def main():
    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        print("No joystick detected.")
        return

    joystick = pygame.joystick.Joystick(0)
    joystick.init()

    print("Joystick detected:")
    print(f"  Name: {joystick.get_name()}")
    print(f"  Axes: {joystick.get_numaxes()}")
    print(f"  Buttons: {joystick.get_numbuttons()}")
    print()
    print("Press L2/R2 slowly. CTRL+C to stop.")
    print()

    previous_axes = [0.0 for _ in range(joystick.get_numaxes())]

    try:
        while True:
            pygame.event.pump()

            axes = [joystick.get_axis(i) for i in range(joystick.get_numaxes())]
            buttons = [joystick.get_button(i) for i in range(joystick.get_numbuttons())]

            changed_axes = []
            for i, value in enumerate(axes):
                if abs(value - previous_axes[i]) > 0.02:
                    changed_axes.append(f"axis {i}: {value:+.3f}")

            previous_axes = axes

            pressed_buttons = [
                str(i)
                for i, value in enumerate(buttons)
                if value == 1
            ]

            if changed_axes or pressed_buttons:
                print(
                    "changed axes: "
                    + ", ".join(changed_axes)
                    + f" || pressed buttons: {pressed_buttons}"
                )

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\nStopped.")

    finally:
        joystick.quit()
        pygame.quit()


if __name__ == "__main__":
    main()