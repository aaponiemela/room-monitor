import sqlite3
from contextlib import closing
from pathlib import Path

from fastapi import FastAPI, HTTPException

app = FastAPI(title="Room Monitor API")

DATABASE_PATH = Path(__file__).resolve().parent / "measurements.sqlite3"


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