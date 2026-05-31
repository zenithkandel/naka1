import { useEffect, useRef, useState } from 'react'

interface CrossingEvent {
  track_id: number
  direction: string
  timestamp: string
  bag_count: number
  bag_types: string
}

export default function LiveFeed() {
  const imgRef = useRef<HTMLImageElement>(null)
  const [connected, setConnected] = useState(false)
  const [events, setEvents] = useState<CrossingEvent[]>([])
  const [stats, setStats] = useState({ todayIn: 0, todayOut: 0, totalTracked: 0 })
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    const ws = new WebSocket(`ws://${window.location.hostname}:5173/ws/events`)
    wsRef.current = ws

    ws.onopen = () => setConnected(true)
    ws.onclose = () => {
      setConnected(false)
      setTimeout(() => {
        const newWs = new WebSocket(`ws://${window.location.hostname}:5173/ws/events`)
        wsRef.current = newWs
      }, 3000)
    }

    ws.onmessage = (msg) => {
      try {
        const event = JSON.parse(msg.data) as CrossingEvent
        setEvents((prev) => [event, ...prev].slice(0, 50))
        setStats((prev) => ({
          ...prev,
          todayIn: prev.todayIn + (event.direction === 'in' ? 1 : 0),
          todayOut: prev.todayOut + (event.direction === 'out' ? 1 : 0),
          totalTracked: prev.totalTracked + 1,
        }))
      } catch {
        // ignore parse errors
      }
    }

    return () => {
      ws.close()
    }
  }, [])

  const streamUrl = `http://${window.location.hostname}:5173/api/v2/stream/live`

  return (
    <div className="main">
      <div className="stream-panel">
        <div className="controls">
          <span style={{ fontSize: 12, color: 'rgba(255,255,255,0.4)', display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: connected ? '#4ade80' : '#f87171', display: 'inline-block' }} />
            {connected ? 'Live' : 'Disconnected'}
          </span>
        </div>
        <div className="stream-container">
          <img
            ref={imgRef}
            src={streamUrl}
            alt="Live feed"
            onError={() => setConnected(false)}
            onLoad={() => setConnected(true)}
          />
        </div>
      </div>

      <div className="sidebar">
        <div className="card">
          <h3>Live Analytics</h3>
          <div className="metrics-grid">
            <div className="metric">
              <div className="value green">{stats.todayIn}</div>
              <div className="label">Entries Today</div>
            </div>
            <div className="metric">
              <div className="value amber">{stats.todayOut}</div>
              <div className="label">Exits Today</div>
            </div>
            <div className="metric">
              <div className="value blue">{stats.totalTracked}</div>
              <div className="label">Total Crossings</div>
            </div>
            <div className="metric">
              <div className="value purple">{stats.todayIn - stats.todayOut}</div>
              <div className="label">Current Occupancy</div>
            </div>
          </div>
        </div>

        <div className="card">
          <h3>Recent Events</h3>
          <div className="events-scroll">
            <div className="event-list">
              {events.length === 0 && (
                <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.3)', padding: 12, textAlign: 'center' }}>
                  Waiting for crossing events...
                </div>
              )}
              {events.map((evt, i) => (
                <div className="event-item" key={`${evt.timestamp}-${evt.track_id}-${i}`}>
                  <span className={`direction-badge ${evt.direction}`}>
                    {evt.direction}
                  </span>
                  <span>ID {evt.track_id}</span>
                  {evt.bag_count > 0 && (
                    <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)' }}>
                      +{evt.bag_count} bag{evt.bag_count > 1 ? 's' : ''}
                    </span>
                  )}
                  <span className="time">
                    {new Date(evt.timestamp).toLocaleTimeString()}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
