from pathlib import Path
from mcap_ros2.reader import read_ros2_messages
import tomllib

CONFIG_FILE = Path("local.config.toml")
with open(CONFIG_FILE, "rb") as f:
    config = tomllib.load(f)

MCAP_FILE = Path(config["mcap"]["file"])

if not MCAP_FILE.exists():
    raise FileNotFoundError(f"MCAP file not found: {MCAP_FILE}")


topics_to_check = [
    "/vehicle/torques",
    "/vehicle/vehicle_state",
    "/vehicle/kinematics",
]

def analyze_mcap_topics():
    for topic in topics_to_check:
        print("\n" + "="*100)
        print(f"Checking topic: {topic}")

        with open(MCAP_FILE, "rb") as f:
            for msg in read_ros2_messages(f, topics=[topic]):
                print(msg.ros_msg)
                break

if __name__ == "__main__":
    analyze_mcap_topics()
