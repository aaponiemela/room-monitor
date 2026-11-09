import { useEffect, useState } from 'react'

type HistoryPoint = {
  received_at: string
  temperature_c: number
}

export default function TemperatureHistory({ latestId }: { latestId: number }) {
  const [history, setHistory] = useState<HistoryPoint[]>([])
  const [error, setError] = useState(false)

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

  if (error) return <p role="alert">Could not load temperature history.</p>
  if (history.length < 2) return <p>Waiting for temperature history…</p>

  const temperatures = history.map((point) => point.temperature_c)
  const low = Math.floor(Math.min(...temperatures))
  const high = Math.max(low + 1, Math.ceil(Math.max(...temperatures)))

  const timestamps = history.map((point) => Date.parse(point.received_at))
  const start = Math.min(...timestamps)
  const end = Math.max(...timestamps)
  const duration = Math.max(1, end - start)

  const line = history.map((point, index) => {
    const x = 64 + ((timestamps[index] - start) / duration) * 552
    const y = 176 - ((point.temperature_c - low) / (high - low)) * 152
    return `${x},${y}`
  }).join(' ')

  const formatTime = (timestamp: number) =>
    new Date(timestamp).toLocaleTimeString('fi-FI')

  return (
    <section className="metric" style={{ marginTop: 24 }}>
      <h2>Temperature history</h2>
      <svg
        viewBox="0 0 640 216"
        width="100%"
        role="img"
        aria-label="Temperature in degrees Celsius over time"
      >
        <path d="M64 24 V176 H616" fill="none" stroke="#607589" />
        <polyline
          points={line}
          fill="none"
          stroke="#72d6bc"
          strokeWidth="3"
        />
        <g fill="currentColor" fontSize="14">
          <text x="54" y="29" textAnchor="end">{high} °C</text>
          <text x="54" y="180" textAnchor="end">{low} °C</text>
          <text x="64" y="202">{formatTime(start)}</text>
          <text x="616" y="202" textAnchor="end">{formatTime(end)}</text>
        </g>
      </svg>
    </section>
  )
}