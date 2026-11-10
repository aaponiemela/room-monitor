import { useEffect, useState } from 'react'

const metrics = {
  temperature_c: { label: 'Temperature', unit: '°C' },
  humidity_pct: { label: 'Humidity', unit: '%' },
  pressure_hpa: { label: 'Pressure', unit: 'hPa' },
} as const

type Metric = keyof typeof metrics

type HistoryPoint = Record<Metric, number> & {
  received_at: string
}

export default function TemperatureHistory({ latestId }: { latestId: number }) {
  const [history, setHistory] = useState<HistoryPoint[]>([])
  const [error, setError] = useState(false)
  const [metric, setMetric] = useState<Metric>('temperature_c')

  useEffect(() => {
    const controller = new AbortController()

    async function loadHistory() {
      try {
        const response = await fetch('/api/measurements/history', {
          signal: controller.signal,
        })

        if (!response.ok) throw new Error(`HTTP ${response.status}`)

        const points: HistoryPoint[] = await response.json()

        if (!controller.signal.aborted) {
          setHistory(points)
          setError(false)
        }
      } catch {
        if (!controller.signal.aborted) setError(true)
      }
    }

    void loadHistory()

    return () => controller.abort()
  }, [latestId])

  if (error) return <p role="alert">Could not load measurement history.</p>
  if (history.length < 2) return <p>Waiting for measurement history…</p>

  const { label, unit } = metrics[metric]
  const values = history.map((point) => point[metric])
  const low = Math.floor(Math.min(...values))
  const high = Math.max(low + 1, Math.ceil(Math.max(...values)))

  const timestamps = history.map((point) => Date.parse(point.received_at))
  const start = Math.min(...timestamps)
  const end = Math.max(...timestamps)
  const duration = Math.max(1, end - start)

  const line = history
    .map((point, index) => {
      const x = 82 + ((timestamps[index] - start) / duration) * 534
      const y = 176 - ((point[metric] - low) / (high - low)) * 152
      return `${x},${y}`
    })
    .join(' ')

  const formatTime = (timestamp: number) =>
    new Date(timestamp).toLocaleTimeString('fi-FI')

  return (
    <section className="metric" style={{ marginTop: 24 }}>
      <h2>Measurement history</h2>

      <label>
        Metric{' '}
        <select
          value={metric}
          onChange={(event) => setMetric(event.target.value as Metric)}
        >
          {Object.entries(metrics).map(([key, { label }]) => (
            <option key={key} value={key}>
              {label}
            </option>
          ))}
        </select>
      </label>

      <svg
        viewBox="0 0 640 216"
        width="100%"
        role="img"
        aria-label={`${label} (${unit}) over time`}
      >
        <path d="M82 24 V176 H616" fill="none" stroke="#607589" />
        <polyline
          points={line}
          fill="none"
          stroke="#72d6bc"
          strokeWidth="3"
        />
        <g fill="currentColor" fontSize="14">
          <text x="72" y="29" textAnchor="end">{high} {unit}</text>
          <text x="72" y="180" textAnchor="end">{low} {unit}</text>
          <text x="82" y="202">{formatTime(start)}</text>
          <text x="616" y="202" textAnchor="end">{formatTime(end)}</text>
        </g>
      </svg>
    </section>
  )
}