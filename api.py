import sqlite3
from contextlib import closing
from pathlib import Path
import os

from fastapi import FastAPI, HTTPException

app = FastAPI(title="Room Monitor API")

PROJECT_ROOT = Path(__file__).resolve().parent

DATABASE_PATH = Path(
    os.environ.get("ROOM_MONITOR_DB", "measurements.sqlite3")
)

if not DATABASE_PATH.is_absolute():
    DATABASE_PATH = PROJECT_ROOT / DATABASE_PATH

DATABASE_PATH = DATABASE_PATH.resolve()


@app.get("/api/measurements/latest")
def get_latest_measurement():
    if not DATABASE_PATH.is_file():
        raise HTTPException(
            status_code=503,
            detail="Database not found. Run the serial reader first.",
        )

    # Read-only mode prevents the API from modifying the database.
    database_uri = DATABASE_PATH.as_uri() + "?mode=ro"

    try:
        with closing(sqlite3.connect(database_uri, uri=True)) as database:
            database.row_factory = sqlite3.Row

            measurement = database.execute("""
                SELECT id, received_at, uptime_ms,
                       temperature_c, humidity_pct, pressure_hpa
                FROM measurements
                ORDER BY id DESC
                LIMIT 1
            """).fetchone()

    except sqlite3.Error:
        raise HTTPException(
            status_code=503,
            detail="Measurement database is unavailable.",
        )

    if measurement is None:
        raise HTTPException(
            status_code=404,
            detail="No measurements stored yet.",
        )

    return dict(measurement)


@app.get("/api/measurements/history")
def get_measurement_history():
    if not DATABASE_PATH.is_file():
        raise HTTPException(
            status_code=503,
            detail="Database not found. Run the serial reader first.",
        )

    database_uri = DATABASE_PATH.as_uri() + "?mode=ro"

    try:
        with closing(sqlite3.connect(database_uri, uri=True)) as database:
            database.row_factory = sqlite3.Row

            measurements = database.execute("""
                SELECT id, received_at, uptime_ms,
                       temperature_c, humidity_pct, pressure_hpa
                FROM measurements
                ORDER BY id DESC
                LIMIT 60
            """).fetchall()

    except sqlite3.Error as error:
        raise HTTPException(
            status_code=503,
            detail="Measurement database is unavailable.",
        ) from error

    return [dict(measurement) for measurement in reversed(measurements)]

@app.get("/api/status")
def get_status():
    return {
        "mode": "demo" if DATABASE_PATH.name == "demo.sqlite3" else "live"
    }