import React from 'react'
import { Menu, X, Play, Pause, Map, Users, Zap, Settings } from 'lucide-react'
import './Sidebar.css'

const SIDEBAR_ITEMS = [
  { id: 'play', icon: Play, label: 'Start' },
  { id: 'pause', icon: Pause, label: 'Stop' },
  { id: 'map', icon: Map, label: 'Tracks' },
  { id: 'agents', icon: Users, label: 'Agents' },
  { id: 'events', icon: Zap, label: 'Events' },
  { id: 'settings', icon: Settings, label: 'Settings' }
]

export default function Sidebar({ isOpen, onToggle }) {
  return (
    <aside className={`sidebar ${isOpen ? 'open' : 'collapsed'}`}>
      <div className="sidebar-header">
        <button className="sidebar-toggle" onClick={onToggle}>
          {isOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      <nav className="sidebar-nav">
        {SIDEBAR_ITEMS.map(item => {
          const IconComponent = item.icon
          return (
            <div key={item.id} className="sidebar-item-wrapper">
              <button className="sidebar-item">
                <IconComponent size={20} />
                {isOpen && <span className="sidebar-label">{item.label}</span>}
              </button>
              {!isOpen && <div className="tooltip">{item.label}</div>}
            </div>
          )
        })}
      </nav>
    </aside>
  )
}
