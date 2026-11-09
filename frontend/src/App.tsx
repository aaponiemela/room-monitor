import { useEffect, useState } from 'react'
import './App.css'
import TemperatureHistory from './TemperatureHistory'

type Measurement = {
  id: number
  received_at: string
  uptime_ms: number
  temperature_c: number
  humidity_pct: number
  pressure_hpa: number
}

function App() {
  const [measurement, setMeasurement] = useState<Measurement | null>(null)
  const [now, setNow] = useState(() => Date.now())
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
  const timer = setInterval(() => {
    setNow(Date.now())
  }, 1000)

  return () => clearInterval(timer)
}, [])

  useEffect(() => {
    const controller = new AbortController()
    let timer: ReturnType<typeof setTimeout> | undefined

    async function fetchMeasurement() {
      try {
        const response = await fetch('/api/measurements/latest', {
          signal: controller.signal,
        })

        if (!response.ok) {
          throw new Error(`API returned status ${response.status}`)
        }

        const data: Measurement = await response.json()

        if (!controller.signal.aborted) {
          setMeasurement(data)
          setError(null)
        }
      } catch {
        if (!controller.signal.aborted) {
          setError('Could not fetch measurements. Check the API server.')
        }
      } finally {
        if (!controller.signal.aborted) {
          timer = setTimeout(fetchMeasurement, 2000)
        }
      }
    }

    void fetchMeasurement()


    return () => {
      controller.abort()
      clearTimeout(timer)
    }
  }, [])

  const measurementAgeMs = measurement
  ? now - new Date(measurement.received_at).getTime()
  : null

const isStale = measurementAgeMs !== null && measurementAgeMs > 15_000

  return (
    <main className="dashboard">
      <header>
        <p className="eyebrow">ARDUINO NICLA SENSE ME</p>
        <h1>Room Monitor</h1>
        <p className="subtitle">Your room, measured.</p>
      </header>

      {error && <p role="alert" className="error">{error}</p>}

      {!measurement && !error && <p>Loading measurements…</p>}

      {measurement && (
        <>
        <p className={`status ${isStale ? 'status-stale' : 'status-fresh'}`}>
  {isStale
    ? 'No recent measurements — check the sensor reader.'
    : 'Measurements received recently'}
</p>

          <section className="metrics" aria-label="Latest measurements">
            <article className="metric">
              <h2>Temperature</h2>
              <p className="value">
                {measurement.temperature_c.toFixed(1)}
                <span> °C</span>
              </p>
            </article>

            <article className="metric">
              <h2>Humidity</h2>
              <p className="value">
                {measurement.humidity_pct.toFixed(0)}
                <span> %</span>
              </p>
            </article>

            <article className="metric">
              <h2>Pressure</h2>
              <p className="value">
                {measurement.pressure_hpa.toFixed(1)}
                <span> hPa</span>
              </p>
            </article>
          </section>
          <TemperatureHistory latestId={measurement.id} />
          <p className="updated">
            Last measurement received:{' '}
            <time dateTime={measurement.received_at}>
              {new Date(measurement.received_at).toLocaleString('fi-FI')}
            </time>
          </p>
        </>
      )}
    </main>
  )
}

export default App