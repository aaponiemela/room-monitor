import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

import api
from serial_reader import open_database, save_measurement


class MeasurementApiTests(unittest.TestCase):
    def setUp(self):
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)

        self.database_path = (
            Path(temporary_directory.name) / "measurements.sqlite3"
        )

        database_patch = patch.object(
            api, "DATABASE_PATH", self.database_path
        )
        database_patch.start()
        self.addCleanup(database_patch.stop)

        self.client = TestClient(api.app)
        self.addCleanup(self.client.close)

    def create_measurements(self, count):
        database = open_database(self.database_path)

        try:
            for index in range(count):
                save_measurement(
                    database,
                    {
                        "uptime_ms": index * 1000,
                        "temperature_c": 20.0 + index / 10,
                        "humidity_pct": 45.0,
                        "pressure_hpa": 1013.0,
                    },
                )
        finally:
            database.close()

    def test_missing_database_returns_503(self):
        for endpoint in ("latest", "history"):
            with self.subTest(endpoint=endpoint):
                response = self.client.get(
                    f"/api/measurements/{endpoint}"
                )
                self.assertEqual(response.status_code, 503)

        self.assertFalse(self.database_path.exists())

    def test_empty_database_returns_404_for_latest(self):
        self.create_measurements(0)

        response = self.client.get("/api/measurements/latest")

        self.assertEqual(response.status_code, 404)

    def test_empty_database_returns_empty_history(self):
        self.create_measurements(0)

        response = self.client.get("/api/measurements/history")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_latest_returns_last_saved_measurement(self):
        self.create_measurements(3)

        response = self.client.get("/api/measurements/latest")

        self.assertEqual(response.status_code, 200)

        measurement = response.json()
        self.assertEqual(measurement["id"], 3)
        self.assertEqual(measurement["uptime_ms"], 2000)
        self.assertAlmostEqual(measurement["temperature_c"], 20.2)
        self.assertEqual(measurement["humidity_pct"], 45.0)
        self.assertEqual(measurement["pressure_hpa"], 1013.0)
        self.assertIn("received_at", measurement)

    def test_history_returns_available_measurements_in_order(self):
        self.create_measurements(3)

        response = self.client.get("/api/measurements/history")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [measurement["id"] for measurement in response.json()],
            [1, 2, 3],
        )

    def test_history_returns_only_60_latest_measurements(self):
        self.create_measurements(65)

        response = self.client.get("/api/measurements/history")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [measurement["id"] for measurement in response.json()],
            list(range(6, 66)),
        )

    def test_invalid_database_returns_503(self):
        self.database_path.write_text(
            "This is not a SQLite database.",
            encoding="utf-8",
        )

        for endpoint in ("latest", "history"):
            with self.subTest(endpoint=endpoint):
                response = self.client.get(
                    f"/api/measurements/{endpoint}"
                )
                self.assertEqual(response.status_code, 503)

    def test_status_returns_live_mode(self):
        response = self.client.get("/api/status")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"mode": "live"})

    def test_status_returns_demo_mode(self):
        demo_path = self.database_path.with_name("demo.sqlite3")

        with patch.object(api, "DATABASE_PATH", demo_path):
            response = self.client.get("/api/status")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"mode": "demo"})


if __name__ == "__main__":
    unittest.main()