import argparse
import json

import serial


def main():
    parser = argparse.ArgumentParser(description="Read Nicla room measurements.")
    parser.add_argument("--port", required=True, help="Serial port, e.g. COM3")
    args = parser.parse_args()

    try:
        with serial.Serial(args.port, baudrate=115200, timeout=2) as connection:
            print(f"Connected to {args.port}. Press Ctrl+C to stop.")

            while True:
                raw_line = connection.readline()

                # A timeout can return an empty or incomplete line.
                if not raw_line or not raw_line.endswith(b"\n"):
                    continue

                try:
                    measurement = json.loads(raw_line.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    print("Skipped an unreadable line.")
                    continue

                print(measurement)

    except serial.SerialException as error:
        print(f"Serial connection error: {error}")
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()