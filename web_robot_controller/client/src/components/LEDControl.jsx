import React, { useState } from 'react'
import './LEDControl.css'

export default function LEDControl({ connected, onSendCommand }) {
  const [color, setColor] = useState('#ff0000')
  const [mode, setMode] = useState('0') // 0=solid, 1=breathing, etc.

  const handleColorChange = (newColor) => {
    setColor(newColor)
    if (connected) {
      const r = parseInt(newColor.slice(1, 3), 16)
      const g = parseInt(newColor.slice(3, 5), 16)
      const b = parseInt(newColor.slice(5, 7), 16)
      onSendCommand(`CMD_LED#${mode}#${r}#${g}#${b}#0`)
    }
  }

  const handleModeChange = (newMode) => {
    setMode(newMode)
    if (connected) {
      const r = parseInt(color.slice(1, 3), 16)
      const g = parseInt(color.slice(3, 5), 16)
      const b = parseInt(color.slice(5, 7), 16)
      onSendCommand(`CMD_LED#${newMode}#${r}#${g}#${b}#0`)
    }
  }

  return (
    <div className="control-section">
      <h3>LED Control</h3>
      <div className="led-controls">
        <div className="led-color-picker">
          <label>Color</label>
          <input
            type="color"
            value={color}
            onChange={(e) => handleColorChange(e.target.value)}
            disabled={!connected}
            className="color-input"
          />
        </div>
        
        <div className="led-mode-selector">
          <label>Mode</label>
          <select
            value={mode}
            onChange={(e) => handleModeChange(e.target.value)}
            disabled={!connected}
            className="mode-select"
          >
            <option value="0">Solid</option>
            <option value="1">Breathing</option>
            <option value="2">Rainbow</option>
            <option value="3">Chase</option>
          </select>
        </div>
      </div>
    </div>
  )
}

