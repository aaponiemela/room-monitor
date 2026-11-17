import math
import sqlite3
import time
from pathlib import Path

from serial_reader import (
    open_database,
    save_measurement,
    validate_measurement,
)

DATABASE_PATH = Path(__file__).resolve().parent / "demo.sqlite3"


def main():
    database = None
    started_at = time.monotonic()

    try:
        database = open_database(DATABASE_PATH)
        print(f"Generating simulated measurements in {DATABASE_PATH}")
        print("Press Ctrl+C to stop.")

        while True:
            elapsed = time.monotonic() - started_at

            measurement = {
                "uptime_ms": int(elapsed * 1000),
                "temperature_c": round(
                    22.5 + 1.5 * math.sin(elapsed / 30), 2
                ),
                "humidity_pct": round(
                    45 + 5 * math.sin(elapsed / 45), 2
                ),
                "pressure_hpa": round(
                    1013 + 2 * math.sin(elapsed / 60), 2
                ),
            }

            validate_measurement(measurement)
            received_at = save_measurement(database, measurement)
            print(f"Simulated measurement at {received_at}: {measurement}")

            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopped.")
    except sqlite3.Error as error:
        print(f"Database error: {error}")
    finally:
        if database is not None:
            database.close()


if __name__ == "__main__":
    main()