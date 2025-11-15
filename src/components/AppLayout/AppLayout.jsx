import React, { useState } from 'react'
import './AppLayout.css'
import Sidebar from '../Sidebar/Sidebar'
import RaceVisualizer from '../RaceVisualizer/RaceVisualizer'
import Leaderboard from '../Leaderboard/Leaderboard'
import TelemetryPanel from '../TelemetryPanel/TelemetryPanel'
import ScenarioConfigModal from '../ScenarioConfigModal/ScenarioConfigModal'

export default function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [showModal, setShowModal] = useState(true)
  const [agents, setAgents] = useState([
    {
      id: 'A1',
      name: 'AlphaBot',
      color: '#00FFD1',
      x: 150,
      y: 150,
      heading: 45,
      speed: 180,
      lap: 2,
      lapTime: 65.34,
      delta: 0,
      status: 'Active'
    },
    {
      id: 'A2',
      name: 'BetaAgent',
      color: '#FFB400',
      x: 250,
      y: 200,
      heading: 90,
      speed: 175,
      lap: 2,
      lapTime: 66.12,
      delta: 0.78,
      status: 'Active'
    },
    {
      id: 'A3',
      name: 'GammaBot',
      color: '#FF6B9D',
      x: 180,
      y: 280,
      heading: 225,
      speed: 168,
      lap: 1,
      lapTime: 64.89,
      delta: -0.45,
      status: 'Warning'
    }
  ])

  const handleStartSimulation = (config) => {
    console.log('Starting simulation with config:', config)
    setShowModal(false)
  }

  // Animate agents on track
  React.useEffect(() => {
    const interval = setInterval(() => {
      setAgents(prevAgents =>
        prevAgents.map(agent => ({
          ...agent,
          x: (agent.x + Math.random() * 10 - 5) % 500,
          y: (agent.y + Math.random() * 10 - 5) % 400,
          heading: (agent.heading + Math.random() * 5 - 2.5) % 360,
          speed: Math.max(160, Math.min(200, agent.speed + Math.random() * 4 - 2))
        }))
      )
    }, 1000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="app-layout">
      <Sidebar isOpen={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} />

      <div className="main-content">
        <div className="center-panel">
          <RaceVisualizer agents={agents} />
        </div>

        <div className="right-panel">
          <div className="leaderboard-container">
            <Leaderboard agents={agents} />
          </div>
          <div className="telemetry-container">
            <TelemetryPanel selectedAgent={agents[0]} />
          </div>
        </div>
      </div>

      <ScenarioConfigModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        onStart={handleStartSimulation}
      />
    </div>
  )
}
