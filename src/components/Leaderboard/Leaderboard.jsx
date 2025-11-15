import React from 'react'
import './Leaderboard.css'

export default function Leaderboard({ agents = [] }) {
  const sortedAgents = [...agents].sort((a, b) => a.lap - b.lap || a.lapTime - b.lapTime)

  return (
    <div className="leaderboard">
      <div className="leaderboard-header">
        <h3>Live Leaderboard</h3>
        <span className="update-badge">Live</span>
      </div>

      <table className="leaderboard-table">
        <thead>
          <tr>
            <th className="col-pos">Pos</th>
            <th className="col-driver">Driver / Agent</th>
            <th className="col-lap">Lap</th>
            <th className="col-time">Lap Time</th>
            <th className="col-speed">Speed</th>
            <th className="col-status">Status</th>
          </tr>
        </thead>
        <tbody>
          {sortedAgents.map((agent, index) => (
            <tr key={agent.id} className={`leaderboard-row ${index % 2 === 0 ? 'even' : 'odd'}`}>
              <td className="col-pos">
                <span className="position">{index + 1}</span>
              </td>
              <td className="col-driver">
                <div className="driver-info">
                  <div className="driver-dot" style={{ backgroundColor: agent.color }} />
                  <span className="driver-name">{agent.name}</span>
                </div>
              </td>
              <td className="col-lap">{agent.lap}</td>
              <td className="col-time">
                <span className="lap-time">{agent.lapTime.toFixed(2)}s</span>
                {agent.delta !== undefined && (
                  <span className={`delta ${agent.delta > 0 ? 'slower' : 'faster'}`}>
                    {agent.delta > 0 ? '+' : ''}{agent.delta.toFixed(2)}s
                  </span>
                )}
              </td>
              <td className="col-speed">
                <span className="speed">{agent.speed} mph</span>
              </td>
              <td className="col-status">
                <span className={`status-badge ${agent.status.toLowerCase()}`}>
                  {agent.status}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
