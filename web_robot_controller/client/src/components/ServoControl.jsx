import React, { useState } from 'react'
import './ServoControl.css'

export default function ServoControl({ connected, onSendCommand }) {
  const [servo1Angle, setServo1Angle] = useState(90)
  const [servo2Angle, setServo2Angle] = useState(90)

  const handleServo1Change = (angle) => {
    setServo1Angle(angle)
    // Servo 1 (LIFT) is index 1 on hardware
    onSendCommand(`CMD_SERVO#1#${angle}`)
  }

  const handleServo2Change = (angle) => {
    setServo2Angle(angle)
    // Servo 2 (CLAW) is index 0 on hardware
    onSendCommand(`CMD_SERVO#0#${angle}`)
  }

  return (
    <div className="control-section">
      <h3>Servo Control</h3>
      <div className="servo-controls">
        <div className="servo-item">
          <label>Lift (Servo 1)</label>
          <div className="servo-slider-container">
            <input
              type="range"
              min="0"
              max="180"
              value={servo1Angle}
              onChange={(e) => handleServo1Change(parseInt(e.target.value))}
              disabled={!connected}
              className="servo-slider"
            />
            <span className="servo-value">{servo1Angle}°</span>
          </div>
        </div>
        
        <div className="servo-item">
          <label>Claw (Servo 2)</label>
          <div className="servo-slider-container">
            <input
              type="range"
              min="0"
              max="180"
              value={servo2Angle}
              onChange={(e) => handleServo2Change(parseInt(e.target.value))}
              disabled={!connected}
              className="servo-slider"
            />
            <span className="servo-value">{servo2Angle}°</span>
          </div>
        </div>
      </div>
    </div>
  )
}

