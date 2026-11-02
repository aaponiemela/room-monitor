# Room Monitor

A room environment monitoring project built with Arduino Nicla Sense ME,
Python, and a planned React frontend.

## Current features

- Temperature, relative humidity, and atmospheric pressure readings
- Newline-delimited JSON output over USB serial
- Python serial reader with JSON parsing
- SQLite storage with UTC reception timestamps
- Measurement validation before storage
- FastAPI endpoint for the latest stored measurement
- Interactive API documentation

## Run the serial reader

Close the Arduino Serial Monitor before starting the reader.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe serial_reader.py --port COM6
```

Replace COM6 with your board's serial port.

## Run the API

```powershell
.\.venv\Scripts\python.exe -m uvicorn api:app --reload
```

Open http://127.0.0.1:8000/docs to explore the API.

Run the serial reader in a separate terminal to collect new measurements.

## Planned features

- FastAPI backend
- React and TypeScript dashboard
- Demo mode without hardware