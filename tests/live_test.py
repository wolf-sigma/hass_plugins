"""
Live integration test for DroneMobile start/stop.

Usage:
    # Create a .env file with your credentials (see below), then:

    uv run python tests/live_test.py                  # read-only: login + list vehicles + status
    uv run python tests/live_test.py --start          # start the engine
    uv run python tests/live_test.py --stop           # stop the engine
    uv run python tests/live_test.py --start --stop   # start, wait, then stop

.env file (create at project root):
    DRONE_MOBILE_USERNAME=your_email@example.com
    DRONE_MOBILE_PASSWORD=your_password
"""

import argparse
import os
import sys
import time
from pathlib import Path

# Load .env from project root
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


def load_env():
    """Load key=value pairs from .env file."""
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())


def main():
    load_env()

    parser = argparse.ArgumentParser(description="Live DroneMobile test")
    parser.add_argument("--start", action="store_true", help="Send remote start command")
    parser.add_argument("--stop", action="store_true", help="Send remote stop command")
    parser.add_argument(
        "--wait",
        type=int,
        default=30,
        help="Seconds to wait between start and stop (default: 30)",
    )
    args = parser.parse_args()

    username = os.environ.get("DRONE_MOBILE_USERNAME")
    password = os.environ.get("DRONE_MOBILE_PASSWORD")

    if not username or not password:
        print("ERROR: Set DRONE_MOBILE_USERNAME and DRONE_MOBILE_PASSWORD")
        print(f"       Either export them or create {ENV_PATH}")
        sys.exit(1)

    from drone_mobile import DroneMobileClient

    # --- Authenticate & fetch vehicles ---
    print(f"Logging in as {username}...")
    with DroneMobileClient(username, password) as client:
        vehicles = client.get_vehicles()
        print(f"Found {len(vehicles)} vehicle(s):\n")

        for i, v in enumerate(vehicles):
            print(f"  [{i}] {v}")
            print(f"      vehicle_id : {v.vehicle_id}")
            print(f"      device_key : {v.device_key}")

            status = v.get_status(use_cache=True)
            if status:
                print(f"      is_running : {status.is_running}")
                print(f"      is_locked  : {status.is_locked}")
                print(f"      battery_v  : {status.battery_voltage}")
                print(f"      int_temp   : {status.interior_temperature}")
                print(f"      odometer   : {status.odometer}")
                if status.location:
                    print(f"      latitude   : {status.location.latitude}")
                    print(f"      longitude  : {status.location.longitude}")
                print(f"      updated    : {status.last_updated}")
            print()

        if not vehicles:
            print("No vehicles found on this account.")
            sys.exit(0)

        vehicle = vehicles[0]
        print(f"Using vehicle: {vehicle}\n")

        # --- Start ---
        if args.start:
            print(">>> Sending START command...")
            resp = vehicle.start()
            print(f"    success: {resp.success}")
            print(f"    response: {resp}\n")

            if args.stop:
                print(f"    Waiting {args.wait}s before stopping...")
                time.sleep(args.wait)

        # --- Stop ---
        if args.stop:
            print(">>> Sending STOP command...")
            resp = vehicle.stop()
            print(f"    success: {resp.success}")
            print(f"    response: {resp}\n")

        # --- Final status ---
        if args.start or args.stop:
            print(">>> Fetching updated status...")
            status = vehicle.get_status()
            print(f"    is_running: {status.is_running}")
            print(f"    is_locked : {status.is_locked}")

    print("\nDone.")


if __name__ == "__main__":
    main()
