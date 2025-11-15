import React, { useState, useEffect } from 'react'
import { ZoomIn, ZoomOut } from 'lucide-react'
import './RaceVisualizer.css'

export default function RaceVisualizer({ agents = [] }) {
  const [zoom, setZoom] = useState(1)
  const [pan, setPan] = useState({ x: 0, y: 0 })

  // Simple track (SVG polygon)
  const trackPoints = [
    { x: 100, y: 100 },
    { x: 400, y: 80 },
    { x: 500, y: 150 },
    { x: 520, y: 300 },
    { x: 400, y: 400 },
    { x: 100, y: 420 },
    { x: 50, y: 250 }
  ]

  const handleZoom = (direction) => {
    setZoom(prev => Math.max(0.5, Math.min(3, prev + (direction === 'in' ? 0.2 : -0.2))))
  }

  return (
    <div className="visualizer">
      <div className="visualizer-header">
        <h2>Race Track</h2>
        <div className="visualizer-controls">
          <button onClick={() => handleZoom('in')} className="zoom-btn">
            <ZoomIn size={18} />
          </button>
          <span className="zoom-level">{(zoom * 100).toFixed(0)}%</span>
          <button onClick={() => handleZoom('out')} className="zoom-btn">
            <ZoomOut size={18} />
          </button>
        </div>
      </div>

      <svg className="track-canvas" viewBox="0 0 600 500" style={{ transform: `scale(${zoom})` }}>
        {/* Track path */}
        <path
          d={`M ${trackPoints.map(p => `${p.x},${p.y}`).join(' L ')} Z`}
          fill="none"
          stroke="rgba(0, 255, 209, 0.3)"
          strokeWidth="8"
          className="track-path"
        />

        {/* Track boundary (inner) */}
        <path
          d={`M ${trackPoints.map(p => `${p.x},${p.y}`).join(' L ')} Z`}
          fill="none"
          stroke="rgba(0, 255, 209, 0.15)"
          strokeWidth="2"
          strokeDasharray="8,4"
          className="track-boundary"
        />

        {/* Agents */}
        {agents.map(agent => (
          <g key={agent.id} className="agent-marker">
            {/* Agent circle */}
            <circle cx={agent.x} cy={agent.y} r="8" fill={agent.color} opacity="0.9" />
            {/* Direction indicator (triangle) */}
            <polygon
              points={`${agent.x},${agent.y - 12} ${agent.x - 8},${agent.y + 8} ${agent.x + 8},${agent.y + 8}`}
              fill={agent.color}
              opacity="0.6"
              style={{
                transform: `rotate(${agent.heading}deg)`,
                transformOrigin: `${agent.x}px ${agent.y}px`,
                transition: 'transform 0.4s ease'
              }}
            />
            {/* ID label */}
            <text x={agent.x + 14} y={agent.y - 6} fontSize="11" fill={agent.color} fontWeight="600">
              {agent.id}
            </text>
          </g>
        ))}
      </svg>

      <div className="visualizer-footer">
        <span className="agent-count">{agents.length} agents on track</span>
      </div>
    </div>
  )
}
