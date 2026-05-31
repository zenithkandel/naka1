import LiveFeed from './components/LiveFeed'

export default function App() {
  return (
    <div className="app">
      <header className="header">
        <h1>BorderVision</h1>
        <span className="badge">v2.0 · LIVE</span>
      </header>
      <LiveFeed />
    </div>
  )
}
