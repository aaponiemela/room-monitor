import argparse
import json
import math
import sqlite3
from datetime import datetime, timezone

import serial


def open_database(path):
    database = sqlite3.connect(path)

    database.execute("""
        CREATE TABLE IF NOT EXISTS measurements (
            id INTEGER PRIMARY KEY,
            received_at TEXT NOT NULL,
            uptime_ms INTEGER NOT NULL,
            temperature_c REAL NOT NULL,
            humidity_pct REAL NOT NULL,
            pressure_hpa REAL NOT NULL
        )
    """)
    database.commit()

    return database


def validate_measurement(measurement):
    if not isinstance(measurement, dict):
        raise ValueError("Measurement must be a JSON object.")

    uptime = measurement.get("uptime_ms")

    if type(uptime) is not int or uptime < 0:
        raise ValueError("uptime_ms must be a non-negative integer.")

    for field in ("temperature_c", "humidity_pct", "pressure_hpa"):
        value = measurement.get(field)

        if type(value) not in (int, float) or not math.isfinite(value):
            raise ValueError(f"{field} must be a finite number.")

    if not 0 <= measurement["humidity_pct"] <= 100:
        raise ValueError("humidity_pct must be between 0 and 100.")

    if measurement["pressure_hpa"] <= 0:
        raise ValueError("pressure_hpa must be positive.")


def save_measurement(database, measurement):
    received_at = datetime.now(timezone.utc).isoformat()

    database.execute(
        """
        INSERT INTO measurements (
            received_at,
            uptime_ms,
            temperature_c,
            humidity_pct,
            pressure_hpa
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            received_at,
            measurement["uptime_ms"],
            measurement["temperature_c"],
            measurement["humidity_pct"],
            measurement["pressure_hpa"],
        ),
    )
    database.commit()

    return received_at


def main():
    parser = argparse.ArgumentParser(description="Read and store Nicla measurements.")
    parser.add_argument("--port", required=True, help="Serial port, e.g. COM6")
    parser.add_argument("--db", default="measurements.sqlite3", help="Database file")
    args = parser.parse_args()

    database = None

    try:
        database = open_database(args.db)

        with serial.Serial(args.port, baudrate=115200, timeout=2) as connection:
            print(f"Connected to {args.port}. Saving to {args.db}.")
            print("Press Ctrl+C to stop.")

            while True:
                raw_line = connection.readline()

                if not raw_line or not raw_line.endswith(b"\n"):
                    continue

                try:
                    measurement = json.loads(raw_line.decode("utf-8"))
                    validate_measurement(measurement)
                except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
                    print(f"Skipped an invalid measurement: {error}")
                    continue

                received_at = save_measurement(database, measurement)
                print(f"Saved at {received_at}: {measurement}")

    except serial.SerialException as error:
        print(f"Serial connection error: {error}")
    except sqlite3.Error as error:
        print(f"Database error: {error}")
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        if database is not None:
            database.close()


if __name__ == "__main__":
    main()