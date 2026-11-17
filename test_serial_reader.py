import unittest
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path

from serial_reader import (
    open_database,
    save_measurement,
    validate_measurement,
)


class ValidateMeasurementTests(unittest.TestCase):
    def setUp(self):
        self.measurement = {
            "uptime_ms": 1000,
            "temperature_c": 22.5,
            "humidity_pct": 45.0,
            "pressure_hpa": 1013.0,
        }

    def test_accepts_valid_measurement(self):
        validate_measurement(self.measurement)

    def test_accepts_humidity_boundaries(self):
        for humidity in (0, 100):
            with self.subTest(humidity=humidity):
                measurement = {
                    **self.measurement,
                    "humidity_pct": humidity,
                }
                validate_measurement(measurement)

    def test_rejects_non_object_input(self):
        for value in (None, [], "measurement", 42):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    validate_measurement(value)

    def test_rejects_missing_fields(self):
        for field in self.measurement:
            with self.subTest(field=field):
                measurement = self.measurement.copy()
                del measurement[field]

                with self.assertRaises(ValueError):
                    validate_measurement(measurement)

    def test_rejects_invalid_uptime(self):
        for uptime in (-1, 1.5, True, "1000"):
            with self.subTest(uptime=uptime):
                measurement = {
                    **self.measurement,
                    "uptime_ms": uptime,
                }

                with self.assertRaises(ValueError):
                    validate_measurement(measurement)

    def test_rejects_invalid_sensor_values(self):
        invalid_values = (
            None,
            "22.5",
            True,
            float("nan"),
            float("inf"),
            float("-inf"),
        )

        for field in ("temperature_c", "humidity_pct", "pressure_hpa"):
            for value in invalid_values:
                with self.subTest(field=field, value=value):
                    measurement = {
                        **self.measurement,
                        field: value,
                    }

                    with self.assertRaises(ValueError):
                        validate_measurement(measurement)

    def test_rejects_humidity_outside_range(self):
        for humidity in (-0.1, 100.1):
            with self.subTest(humidity=humidity):
                measurement = {
                    **self.measurement,
                    "humidity_pct": humidity,
                }

                with self.assertRaises(ValueError):
                    validate_measurement(measurement)

    def test_rejects_non_positive_pressure(self):
        for pressure in (0, -1):
            with self.subTest(pressure=pressure):
                measurement = {
                    **self.measurement,
                    "pressure_hpa": pressure,
                }

                with self.assertRaises(ValueError):
                    validate_measurement(measurement)


class MeasurementStorageTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_directory.cleanup)

        self.database_path = (
            Path(self.temp_directory.name) / "measurements.sqlite3"
        )

        self.measurement = {
            "uptime_ms": 1000,
            "temperature_c": 22.5,
            "humidity_pct": 45.0,
            "pressure_hpa": 1013.0,
        }

    def test_saves_values_and_utc_timestamp(self):
        database = open_database(self.database_path)

        try:
            received_at = save_measurement(database, self.measurement)

            row = database.execute("""
                SELECT received_at, uptime_ms, temperature_c,
                       humidity_pct, pressure_hpa
                FROM measurements
            """).fetchone()

            self.assertEqual(
                row,
                (
                    received_at,
                    1000,
                    22.5,
                    45.0,
                    1013.0,
                ),
            )

            timestamp = datetime.fromisoformat(received_at)
            self.assertIsNotNone(timestamp.utcoffset())
            self.assertEqual(timestamp.utcoffset().total_seconds(), 0)
        finally:
            database.close()

    def test_preserves_measurements_after_reopening(self):
        database = open_database(self.database_path)

        try:
            save_measurement(database, self.measurement)
        finally:
            database.close()

        database = open_database(self.database_path)

        try:
            save_measurement(
                database,
                {**self.measurement, "temperature_c": 23.0},
            )
        finally:
            database.close()

        with sqlite3.connect(self.database_path) as database:
            rows = database.execute("""
                SELECT temperature_c
                FROM measurements
                ORDER BY id
            """).fetchall()

        self.assertEqual(rows, [(22.5,), (23.0,)])

if __name__ == "__main__":
    unittest.main()