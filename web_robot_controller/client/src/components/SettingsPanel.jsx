import React from 'react'
import { X } from 'lucide-react'
import './SettingsPanel.css'

export default function SettingsPanel({ settings, onChange, onClose }) {
  return (
    <div className="settings-overlay" onClick={onClose}>
      <div className="settings-panel" onClick={(e) => e.stopPropagation()}>
        <div className="settings-header">
          <h2>Connection Settings</h2>
          <button className="close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>
        
        <div className="settings-content">
          <div className="setting-item">
            <label>Robot IP Address</label>
            <input
              type="text"
              value={settings.ip}
              onChange={(e) => onChange({ ...settings, ip: e.target.value })}
              placeholder="10.0.0.86"
            />
          </div>
          
          <div className="setting-item">
            <label>Command Port</label>
            <input
              type="number"
              value={settings.commandPort}
              onChange={(e) => onChange({ ...settings, commandPort: e.target.value })}
              placeholder="5003"
            />
          </div>
          
          <div className="setting-item">
            <label>Video Port</label>
            <input
              type="number"
              value={settings.videoPort}
              onChange={(e) => onChange({ ...settings, videoPort: e.target.value })}
              placeholder="8003"
            />
          </div>
        </div>
      </div>
    </div>
  )
}

