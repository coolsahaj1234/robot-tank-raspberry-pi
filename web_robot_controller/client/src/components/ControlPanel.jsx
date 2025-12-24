import React, { useState, useEffect, useRef } from 'react'
import { ArrowUp, ArrowDown, ArrowLeft, ArrowRight, GripVertical, AlertTriangle } from 'lucide-react'
import ServoControl from './ServoControl'
import LEDControl from './LEDControl'
import { useMovementIntelligence } from '../hooks/useMovementIntelligence'
import './ControlPanel.css'

export default function ControlPanel({ connected, onSendCommand, videoFrame, sensorData, currentMode }) {
  const [pressedKeys, setPressedKeys] = useState(new Set())
  const [speed, setSpeed] = useState(50)
  const dpadTimeoutRef = useRef(null)
  
  // Intelligent movement control
  const { effectiveSpeed, isStuck, obstacleDetected } = useMovementIntelligence({
    connected,
    videoFrame,
    sensorData,
    currentMode,
    baseSpeed: speed,
    onSendCommand
  })
  
  // Use effective speed for motor commands in Move mode
  const motorSpeed = currentMode === '1' ? effectiveSpeed : speed

  // Keyboard controls
  useEffect(() => {
    if (!connected) return

    const handleKeyDown = (e) => {
      const key = e.key
      if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(key)) {
        e.preventDefault()
        setPressedKeys(prev => new Set([...prev, key]))
      }
    }

    const handleKeyUp = (e) => {
      const key = e.key
      if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(key)) {
        e.preventDefault()
        setPressedKeys(prev => {
          const next = new Set(prev)
          next.delete(key)
          return next
        })
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    window.addEventListener('keyup', handleKeyUp)

    return () => {
      window.removeEventListener('keydown', handleKeyDown)
      window.removeEventListener('keyup', handleKeyUp)
    }
  }, [connected])

  // Track if we've set manual mode
  const manualModeSetRef = useRef(false)

  // Set manual mode once when connected
  useEffect(() => {
    if (connected && !manualModeSetRef.current) {
      // CMD_MODE#0 sets car_mode to 1 (manual control mode)
      // Mode 1 = manual control (just reads sensors, doesn't auto-control motors)
      onSendCommand('CMD_MODE#0')
      manualModeSetRef.current = true
    } else if (!connected) {
      manualModeSetRef.current = false
    }
  }, [connected, onSendCommand])

  // Convert speed percentage (-100 to 100) to motor duty cycle (-4095 to 4095)
  // Motor accepts full range -4095 to 4095
  // Scale: 100% speed = 4095 duty cycle (full power), so multiply by 40.95
  // Using 40.95 to map 100% to ~4095 (will be clamped by motor driver)
  const scaleToMotorValue = (speedPercent) => {
    // Scale from -100..100 to -4095..4095 (full motor power range)
    // This honors the power slider - 100% = full power, 50% = half power, etc.
    return Math.round(speedPercent * 40.95)
  }

  // Send motor commands based on pressed keys
  useEffect(() => {
    if (!connected) {
      return // Don't send commands if not connected
    }
    
    if (pressedKeys.size === 0) {
      onSendCommand('CMD_MOTOR#0#0')
      return
    }

    let x = 0
    let y = 0

    if (pressedKeys.has('ArrowUp')) y += 1
    if (pressedKeys.has('ArrowDown')) y -= 1
    if (pressedKeys.has('ArrowLeft')) x -= 1
    if (pressedKeys.has('ArrowRight')) x += 1

    // Improved turning: use full differential for better turning ability
    const turnFactor = 0.8  // 80% differential for turning (was 0.5 = 50%)
    const leftSpeedPercent = (y * speed) + (x * speed * turnFactor)
    const rightSpeedPercent = (y * speed) - (x * speed * turnFactor)

    const clampedLeftPercent = Math.max(-100, Math.min(100, leftSpeedPercent))
    const clampedRightPercent = Math.max(-100, Math.min(100, rightSpeedPercent))

    // Convert to motor duty cycle values (use effective speed in Move mode)
    const leftMotorValue = scaleToMotorValue(clampedLeftPercent * (motorSpeed / 100))
    const rightMotorValue = scaleToMotorValue(clampedRightPercent * (motorSpeed / 100))

    // Don't send mode command - we're already in manual mode
    // Just send motor commands
    onSendCommand(`CMD_MOTOR#${leftMotorValue}#${rightMotorValue}`)
  }, [pressedKeys, motorSpeed, connected, onSendCommand])

  const handleDirectionClick = (x, y) => {
    if (!connected) {
      console.warn('⚠️ Cannot send command: not connected')
      return
    }
    
    console.log(`🎮 D-pad clicked: x=${x}, y=${y}, speed=${speed}`)
    
    // Clear any existing timeout
    if (dpadTimeoutRef.current) {
      clearTimeout(dpadTimeoutRef.current)
      dpadTimeoutRef.current = null
    }
    
    // Clear any pressed keys to prevent keyboard controls from interfering
    setPressedKeys(new Set())
    
    // Ensure we're in manual mode (CMD_MODE#0 = manual control, doesn't auto-control motors)
    // Always ensure mode is set before sending motor commands
    if (!manualModeSetRef.current) {
      console.log('📡 Setting manual mode (CMD_MODE#0)')
      onSendCommand('CMD_MODE#0')
      manualModeSetRef.current = true
      // Small delay to ensure mode is set before motor command
      setTimeout(() => {
        sendMotorCommand(x, y)
      }, 50)
    } else {
      sendMotorCommand(x, y)
    }
  }

  const sendMotorCommand = (x, y) => {
    // Improved turning: use full differential for better turning ability
    const turnFactor = 0.8  // 80% differential for turning (was 0.5 = 50%)
    const leftSpeedPercent = (y * speed) + (x * speed * turnFactor)
    const rightSpeedPercent = (y * speed) - (x * speed * turnFactor)
    
    const clampedLeftPercent = Math.max(-100, Math.min(100, leftSpeedPercent))
    const clampedRightPercent = Math.max(-100, Math.min(100, rightSpeedPercent))
    
    // Convert to motor duty cycle values (use effective speed in Move mode)
    const leftMotorValue = scaleToMotorValue(clampedLeftPercent * (motorSpeed / 100))
    const rightMotorValue = scaleToMotorValue(clampedRightPercent * (motorSpeed / 100))
    
    console.log(`📤 Sending motor command: left=${leftMotorValue} (${clampedLeftPercent}% @ ${motorSpeed}%), right=${rightMotorValue} (${clampedRightPercent}% @ ${motorSpeed}%)`)
    
    // Send movement command
    onSendCommand(`CMD_MOTOR#${leftMotorValue}#${rightMotorValue}`)
    
    // Stop after 100ms - use ref to ensure it's called
    dpadTimeoutRef.current = setTimeout(() => {
      if (connected) {
        console.log('🛑 Stopping motors')
        onSendCommand('CMD_MOTOR#0#0')
      }
      dpadTimeoutRef.current = null
    }, 100)
  }
  
  // Cleanup timeout on unmount or disconnect
  useEffect(() => {
    return () => {
      if (dpadTimeoutRef.current) {
        clearTimeout(dpadTimeoutRef.current)
        dpadTimeoutRef.current = null
      }
    }
  }, [])
  
  // Stop motors when disconnecting
  useEffect(() => {
    if (!connected && dpadTimeoutRef.current) {
      clearTimeout(dpadTimeoutRef.current)
      dpadTimeoutRef.current = null
      onSendCommand('CMD_MOTOR#0#0')
    }
  }, [connected, onSendCommand])

  return (
    <div className="control-panel">
      <div className="control-section movement-section">
        <div className="movement-header">
          <h3>Movement</h3>
          <div className="speed-control-compact">
            <label>Speed</label>
            <div className={`speed-display ${currentMode === '1' && effectiveSpeed !== speed ? 'adjusted' : ''}`}>
              {currentMode === '1' ? `${effectiveSpeed}%` : `${speed}%`}
              {currentMode === '1' && effectiveSpeed < speed && (
                <span className="speed-hint" title={`Base: ${speed}% - Auto-adjusted for safety`}>
                  <AlertTriangle size={12} />
                </span>
              )}
            </div>
            <input
              type="range"
              min="10"
              max="100"
              value={speed}
              onChange={(e) => setSpeed(parseInt(e.target.value))}
              className="speed-slider-compact"
            />
          </div>
        </div>
        
        {currentMode === '1' && (isStuck || obstacleDetected) && (
          <div className="movement-status">
            {isStuck && <span className="status-badge stuck">⚠️ Stuck Detected</span>}
            {obstacleDetected && <span className="status-badge obstacle">🚧 Obstacle Near</span>}
          </div>
        )}
        
        <div className="dpad-container-compact">
          <div className="dpad-compact">
            <button
              className="dpad-btn-compact dpad-up"
              onClick={() => handleDirectionClick(0, 1)}
              disabled={!connected}
            >
              <ArrowUp size={16} />
            </button>
            <div className="dpad-middle-compact">
              <button
                className="dpad-btn-compact dpad-left"
                onClick={() => handleDirectionClick(-1, 0)}
                disabled={!connected}
              >
                <ArrowLeft size={16} />
              </button>
              <button
                className="dpad-btn-compact dpad-center"
                onClick={() => onSendCommand('CMD_MOTOR#0#0')}
                disabled={!connected}
              >
                <GripVertical size={14} />
              </button>
              <button
                className="dpad-btn-compact dpad-right"
                onClick={() => handleDirectionClick(1, 0)}
                disabled={!connected}
              >
                <ArrowRight size={16} />
              </button>
            </div>
            <button
              className="dpad-btn-compact dpad-down"
              onClick={() => handleDirectionClick(0, -1)}
              disabled={!connected}
            >
              <ArrowDown size={16} />
            </button>
          </div>
          <div className="keyboard-hint-compact">
            Arrow keys for continuous
          </div>
        </div>
      </div>

      <ServoControl connected={connected} onSendCommand={onSendCommand} />
      <LEDControl connected={connected} onSendCommand={onSendCommand} />
    </div>
  )
}

