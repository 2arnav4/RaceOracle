import React, { useState } from 'react'
import './TelemetryPanel.css'

export default function TelemetryPanel({ selectedAgent = null }) {
  const [activeTab, setActiveTab] = useState('status')

  const mockTelemetry = selectedAgent || {
    battery: 85,
    engineTemp: 92,
    tireWear: 45,
    speed: 180,
    gForce: 2.3
  }

  const mockEvents = [
    { lap: 5, message: '⚠ Engine overheating. Performance reduced.', time: '02:34' },
    { lap: 4, message: '🌧 Rain starting. Grip -30%', time: '02:12' },
    { lap: 3, message: '✓ Pit stop completed. New tires mounted.', time: '01:45' },
    { lap: 2, message: '⚡ Power management engaged.', time: '01:20' },
    { lap: 1, message: '🏁 Race started. Good luck!', time: '00:00' }
  ]

  return (
    <div className="telemetry-panel">
      <div className="telemetry-header">
        <h3>Telemetry</h3>
      </div>

      <div className="telemetry-tabs">
        <button
          className={`tab-btn ${activeTab === 'status' ? 'active' : ''}`}
          onClick={() => setActiveTab('status')}
        >
          Status
        </button>
        <button
          className={`tab-btn ${activeTab === 'graph' ? 'active' : ''}`}
          onClick={() => setActiveTab('graph')}
        >
          Speed
        </button>
        <button
          className={`tab-btn ${activeTab === 'events' ? 'active' : ''}`}
          onClick={() => setActiveTab('events')}
        >
          Events
        </button>
      </div>

      <div className="telemetry-content">
        {activeTab === 'status' && (
          <div className="status-bars">
            <div className="bar-group">
              <label>Battery</label>
              <div className="bar-container">
                <div className="bar-fill" style={{ width: `${mockTelemetry.battery}%`, background: 'linear-gradient(90deg, #00FFD1, #00d9b0)' }} />
              </div>
              <span className="bar-value">{mockTelemetry.battery}%</span>
            </div>

            <div className="bar-group">
              <label>Engine Temp</label>
              <div className="bar-container">
                <div className="bar-fill" style={{ width: `${mockTelemetry.engineTemp}%`, background: mockTelemetry.engineTemp > 90 ? 'linear-gradient(90deg, #FFB400, #ff9600)' : 'linear-gradient(90deg, #FFB400, #ffc844)' }} />
              </div>
              <span className="bar-value">{mockTelemetry.engineTemp}°C</span>
            </div>

            <div className="bar-group">
              <label>Tire Wear</label>
              <div className="bar-container">
                <div className="bar-fill" style={{ width: `${mockTelemetry.tireWear}%`, background: 'linear-gradient(90deg, #ff8c42, #ff6b42)' }} />
              </div>
              <span className="bar-value">{mockTelemetry.tireWear}%</span>
            </div>

            <div className="metrics-grid">
              <div className="metric">
                <span className="metric-label">Speed</span>
                <span className="metric-value">{mockTelemetry.speed} mph</span>
              </div>
              <div className="metric">
                <span className="metric-label">G Force</span>
                <span className="metric-value">{mockTelemetry.gForce}G</span>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'graph' && (
          <div className="speed-graph">
            <svg viewBox="0 0 300 120">
              <polyline
                points="10,110 40,90 70,75 100,85 130,65 160,70 190,55 220,60 250,50 280,45"
                fill="none"
                stroke="var(--accent-primary)"
                strokeWidth="2"
                vectorEffect="non-scaling-stroke"
              />
              <polyline
                points="10,110 40,90 70,75 100,85 130,65 160,70 190,55 220,60 250,50 280,45"
                fill="url(#gradientFill)"
                opacity="0.2"
              />
              <defs>
                <linearGradient id="gradientFill" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stopColor="var(--accent-primary)" stopOpacity="0.4" />
                  <stop offset="100%" stopColor="var(--accent-primary)" stopOpacity="0" />
                </linearGradient>
              </defs>
            </svg>
            <p className="graph-label">Speed over last 20 seconds (simulated)</p>
          </div>
        )}

        {activeTab === 'events' && (
          <div className="event-log">
            {mockEvents.map((event, idx) => (
              <div key={idx} className="event-line">
                <span className="event-time">{event.time}</span>
                <span className="event-lap">[LAP {event.lap}]</span>
                <span className="event-message">{event.message}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
