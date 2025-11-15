// src/App.jsx
import React, { useEffect, useState } from 'react'
import RaceVisualizer from './components/RaceVisualizer'
import './styles/globals.css'

function App() {
  const [agents, setAgents] = useState([])
  const [eventLog, setEventLog] = useState([])
  const [simStatus, setSimStatus] = useState('idle')

  // Start simulation once on mount
  useEffect(() => {
    const start = async () => {
      try {
        await fetch('http://127.0.0.1:8000/simulation/start', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({}),
        })
        setSimStatus('running')
      } catch (err) {
        console.error('Failed to start simulation', err)
        setSimStatus('error')
      }
    }
    start()
  }, [])

  // Poll state every 200ms
  useEffect(() => {
    if (simStatus !== 'running') return

    const interval = setInterval(async () => {
      try {
        const res = await fetch('http://127.0.0.1:8000/simulation/state')
        const data = await res.json()
        if (data && data.agents) {
          setAgents(
            data.agents.map(a => ({
              id: a.id,
              x: a.x,
              y: a.y,
              color: a.color,
              heading: a.heading,
            }))
          )
          setEventLog(data.event_log || [])
        }
      } catch (err) {
        console.error('Failed to fetch state', err)
      }
    }, 200)

    return () => clearInterval(interval)
  }, [simStatus])

  return (
    <div className="app">
      <header className="app-header">
        <h1>Race Oracle</h1>
        <span className={`status status-${simStatus}`}>{simStatus.toUpperCase()}</span>
      </header>
      <main className="app-main">
        <RaceVisualizer agents={agents} />
        <div className="event-log">
          <h3>Events</h3>
          <div className="event-log-body">
            {eventLog.slice().reverse().map((e, idx) => (
              <div key={idx} className="event-line">
                {e}
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
