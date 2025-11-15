import React, { useState } from 'react'
import { X } from 'lucide-react'
import './ScenarioConfigModal.css'

export default function ScenarioConfigModal({ isOpen, onClose, onStart }) {
  const [selectedTrack, setSelectedTrack] = useState('monaco')
  const [agents, setAgents] = useState([
    { id: 'a1', name: 'AlphaBot', param: 'aggressive' },
    { id: 'a2', name: 'BetaAgent', param: 'balanced' },
    { id: 'a3', name: 'GammaBot', param: 'conservative' }
  ])

  const tracks = [
    { value: 'monaco', label: 'Monaco' },
    { value: 'silverstone', label: 'Silverstone' },
    { value: 'spa', label: 'Spa' },
    { value: 'monza', label: 'Monza' }
  ]

  const handleAgentChange = (id, field, value) => {
    setAgents(agents.map(a => a.id === id ? { ...a, [field]: value } : a))
  }

  const handleAddAgent = () => {
    const newId = `a${Math.random().toString(36).substr(2, 9)}`
    setAgents([...agents, { id: newId, name: `Agent-${agents.length + 1}`, param: 'balanced' }])
  }

  const handleRemoveAgent = (id) => {
    setAgents(agents.filter(a => a.id !== id))
  }

  const handleStart = () => {
    onStart({ track: selectedTrack, agents })
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="modal-backdrop">
      <div className="modal-content">
        <div className="modal-header">
          <h2>Race Configuration</h2>
          <button className="modal-close" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div className="modal-body">
          <div className="config-section">
            <label className="section-label">Track</label>
            <select
              value={selectedTrack}
              onChange={(e) => setSelectedTrack(e.target.value)}
              className="track-select"
            >
              {tracks.map(t => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>

          <div className="config-section">
            <label className="section-label">Agents</label>
            <div className="agents-list">
              {agents.map(agent => (
                <div key={agent.id} className="agent-row">
                  <input
                    type="text"
                    value={agent.name}
                    onChange={(e) => handleAgentChange(agent.id, 'name', e.target.value)}
                    className="agent-input"
                    placeholder="Agent name"
                  />
                  <select
                    value={agent.param}
                    onChange={(e) => handleAgentChange(agent.id, 'param', e.target.value)}
                    className="agent-select"
                  >
                    <option value="aggressive">Aggressive</option>
                    <option value="balanced">Balanced</option>
                    <option value="conservative">Conservative</option>
                  </select>
                  <button
                    className="remove-btn"
                    onClick={() => handleRemoveAgent(agent.id)}
                    title="Remove agent"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
            <button className="add-agent-btn" onClick={handleAddAgent}>
              + Add Agent
            </button>
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn-primary" onClick={handleStart}>Start Simulation</button>
        </div>
      </div>
    </div>
  )
}
