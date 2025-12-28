import React, { useState } from 'react'
import './ModeSelector.css'

const MODES = [
  { value: '0', label: 'Stop' },
  { value: '1', label: 'Move' },
  { value: '2', label: 'Sonar' },
  { value: '3', label: 'Infrared' },
<<<<<<< HEAD
  { value: '4', label: 'AI Auto' }
=======
  { value: '4', label: 'AI Auto' },
  { value: '5', label: '🎅 Santa' },
  { value: '6', label: '🅿️ AutoPark' }
>>>>>>> 40885bf (Initial commit)
]

export default function ModeSelector({ connected, onSendCommand, onModeChange }) {
  const [selectedMode, setSelectedMode] = useState('0')
<<<<<<< HEAD
  
=======

>>>>>>> 40885bf (Initial commit)
  const handleModeChange = (mode) => {
    setSelectedMode(mode)
    onSendCommand(`CMD_MODE#${mode}`)
    if (onModeChange) {
      onModeChange(mode)
    }
  }

  return (
    <div className="mode-selector-bottom">
      <div className="mode-label">Robot Mode:</div>
      <div className="mode-buttons">
        {MODES.map(mode => (
          <button
            key={mode.value}
            className={`mode-btn ${selectedMode === mode.value ? 'active' : ''}`}
            onClick={() => handleModeChange(mode.value)}
            disabled={!connected}
          >
            {mode.label}
          </button>
        ))}
      </div>
    </div>
  )
}

