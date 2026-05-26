
import json
import socket
import time

import pygame


UDP_IP = "172.27.151.229"
UDP_PORT = 9999

DT = 0.05  # 20 Hz


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
    print()
    print(f"Sending UDP to {UDP_IP}:{UDP_PORT}")
    print("Press CTRL+C to stop.")
    print()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        while True:
            loop_start = time.time()

            pygame.event.pump()

            axes = [
                float(joystick.get_axis(i))
                for i in range(joystick.get_numaxes())
            ]

            buttons = [
                int(joystick.get_button(i))
                for i in range(joystick.get_numbuttons())
            ]

            payload = {
                "axes": axes,
                "buttons": buttons,
            }

            data = json.dumps(payload).encode("utf-8")
            sock.sendto(data, (UDP_IP, UDP_PORT))

            print(
                f"axis0={axes[0]:+.3f} "
                f"axis3={axes[3]:+.3f} "
            )

            elapsed = time.time() - loop_start
            time.sleep(max(0.0, DT - elapsed))

    except KeyboardInterrupt:
        print("\nStopped.")

    finally:
        joystick.quit()
        pygame.quit()
        sock.close()


if __name__ == "__main__":
    main()