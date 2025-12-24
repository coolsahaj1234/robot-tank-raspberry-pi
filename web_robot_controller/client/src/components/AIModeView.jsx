import React, { useState, useEffect, useRef, useCallback } from 'react'
import VideoView from './VideoView'
import RadarView from './RadarView'
import { Activity, AlertCircle, Navigation, Gauge, Shield, Eye, Brain, ArrowUp, ArrowDown, ArrowLeft, ArrowRight, MessageCircle, Bot, MousePointer, Target, Send, Play, Square, Mic } from 'lucide-react'
import './AIModeView.css'

export default function AIModeView({
  videoFrame,
  processedFrame,
  connected,
  sensorData,
  settings,
  navigationCommand,
  laneData,
  obstacleData,
  radarData,
  navigationState,
  aiProcessing,
  aiError,
  thinkingLog = [],
  narration = '',
  detectedObjects = [],
  onSendCommand,
  onSetAutonomousEnabled
}) {
  const dangerZone = obstacleData?.danger_zone || navigationCommand?.danger_zone || 'clear'
  const logContainerRef = useRef(null)
  const chatContainerRef = useRef(null)
  const liveFeedRef = useRef(null)
  const inputRef = useRef(null)
  const [narrationHistory, setNarrationHistory] = useState([])
  const lastNarrationRef = useRef('')

  // Conversation state
  const [chatMessages, setChatMessages] = useState([
    { role: 'assistant', text: "Hello! I'm your AI companion. Tell me what you'd like me to do - say 'start exploring' to begin autonomous navigation, or give me specific commands like 'turn left' or 'move forward'.", timestamp: Date.now() }
  ])
  const [userInput, setUserInput] = useState('')
  const [isAutonomousRunning, setIsAutonomousRunning] = useState(false)

  // Click-to-navigate state
  const [clickTarget, setClickTarget] = useState(null)
  const [isManualMode, setIsManualMode] = useState(false)
  const manualCommandTimeoutRef = useRef(null)

  // Track narration from AI when autonomous mode is running
  useEffect(() => {
    if (narration && narration !== lastNarrationRef.current && narration.length > 5 && isAutonomousRunning) {
      lastNarrationRef.current = narration
      // Add AI narration as assistant message
      setChatMessages(prev => [...prev, { role: 'assistant', text: narration, timestamp: Date.now() }].slice(-20))
    }
  }, [narration, isAutonomousRunning])

  // Notify parent of autonomous state changes
  useEffect(() => {
    if (onSetAutonomousEnabled) {
      onSetAutonomousEnabled(isAutonomousRunning)
    }
  }, [isAutonomousRunning, onSetAutonomousEnabled])

  // Handle user command input
  const handleSendCommand = useCallback(() => {
    if (!userInput.trim() || !connected) return

    const command = userInput.trim().toLowerCase()
    const userMessage = { role: 'user', text: userInput.trim(), timestamp: Date.now() }
    setChatMessages(prev => [...prev, userMessage].slice(-20))
    setUserInput('')

    // Parse and execute command
    let response = ''

    // Start/Stop autonomous navigation
    if (command.includes('start') || command.includes('explore') || command.includes('go') && command.includes('auto')) {
      setIsAutonomousRunning(true)
      response = "Starting autonomous exploration! I'll navigate around and tell you what I see. Say 'stop' anytime to pause."
    }
    else if (command.includes('stop') || command.includes('halt') || command.includes('pause')) {
      setIsAutonomousRunning(false)
      if (onSendCommand) {
        onSendCommand({ type: 'move', direction: 'stop', speed: 0 })
      }
      response = "Stopping. I'll wait here for your next command."
    }
    // Direct movement commands
    else if (command.includes('forward') || command.includes('ahead') || command.includes('straight')) {
      if (onSendCommand) {
        onSendCommand({ type: 'move', direction: 'forward', speed: 50 })
        setTimeout(() => onSendCommand({ type: 'move', direction: 'stop', speed: 0 }), 1000)
      }
      response = "Moving forward..."
    }
    else if (command.includes('back') || command.includes('reverse') || command.includes('retreat')) {
      if (onSendCommand) {
        onSendCommand({ type: 'move', direction: 'backward', speed: 50 })
        setTimeout(() => onSendCommand({ type: 'move', direction: 'stop', speed: 0 }), 1000)
      }
      response = "Backing up..."
    }
    else if (command.includes('left')) {
      if (onSendCommand) {
        onSendCommand({ type: 'move', direction: 'left', speed: 60 })
        setTimeout(() => onSendCommand({ type: 'move', direction: 'stop', speed: 0 }), 800)
      }
      response = "Turning left..."
    }
    else if (command.includes('right')) {
      if (onSendCommand) {
        onSendCommand({ type: 'move', direction: 'right', speed: 60 })
        setTimeout(() => onSendCommand({ type: 'move', direction: 'stop', speed: 0 }), 800)
      }
      response = "Turning right..."
    }
    // Status queries
    else if (command.includes('what') && (command.includes('see') || command.includes('around'))) {
      const distance = sensorData?.distance || radarData?.ultrasonic_distance || 0
      const objects = detectedObjects.length > 0
        ? detectedObjects.map(o => o.type.toLowerCase()).join(', ')
        : 'nothing specific'
      response = `I can see ${objects} in front of me. The nearest obstacle is about ${Math.round(distance)}cm away.`
    }
    else if (command.includes('status') || command.includes('how are you')) {
      const distance = sensorData?.distance || radarData?.ultrasonic_distance || 0
      response = `I'm ${isAutonomousRunning ? 'actively exploring' : 'waiting for commands'}. Front clearance: ${Math.round(distance)}cm. ${dangerZone === 'danger' ? '⚠️ Obstacle very close!' : dangerZone === 'caution' ? 'Something nearby, being careful.' : 'Path looks clear.'}`
    }
    // Help
    else if (command.includes('help') || command.includes('commands') || command.includes('what can')) {
      response = "I understand: 'start exploring', 'stop', 'turn left/right', 'move forward/back', 'what do you see?', and 'status'. You can also click on the video feed to navigate!"
    }
    else {
      response = `I'm not sure what you mean by "${userInput.trim()}". Try 'start exploring', 'stop', 'turn left', 'move forward', or ask 'what do you see?'`
    }

    // Add assistant response
    setTimeout(() => {
      setChatMessages(prev => [...prev, { role: 'assistant', text: response, timestamp: Date.now() }].slice(-20))
    }, 300)
  }, [userInput, connected, onSendCommand, sensorData, radarData, detectedObjects, dangerZone, isAutonomousRunning])

  // Handle Enter key
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendCommand()
    }
  }

  // Auto-scroll log to bottom
  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight
    }
  }, [thinkingLog])

  // Auto-scroll chat to bottom when new messages arrive
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight
    }
  }, [chatMessages])

  // Clean up manual mode timeout on unmount
  useEffect(() => {
    return () => {
      if (manualCommandTimeoutRef.current) {
        clearTimeout(manualCommandTimeoutRef.current)
      }
    }
  }, [])

  // Handle click-to-navigate on the live feed
  const handleVideoClick = useCallback((e) => {
    if (!connected || !onSendCommand) return

    const rect = e.currentTarget.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top
    const width = rect.width
    const height = rect.height

    // Calculate relative position (0-1)
    const relX = x / width
    const relY = y / height

    // Set click target for visual feedback
    setClickTarget({ x, y, relX, relY, timestamp: Date.now() })

    // Enter manual mode temporarily
    setIsManualMode(true)

    // Determine navigation command based on click position
    let direction = null
    let speed = 50

    // Horizontal: left third = turn left, right third = turn right, middle = forward
    if (relX < 0.33) {
      direction = 'left'
      speed = 70
    } else if (relX > 0.67) {
      direction = 'right'
      speed = 70
    } else {
      // Vertical: top = forward fast, middle = forward, bottom = backward
      if (relY < 0.4) {
        direction = 'forward'
        speed = 60
      } else if (relY > 0.7) {
        direction = 'backward'
        speed = 50
      } else {
        direction = 'forward'
        speed = 45
      }
    }

    // Send manual navigation command
    if (direction === 'forward') {
      onSendCommand({ type: 'move', direction: 'forward', speed })
    } else if (direction === 'backward') {
      onSendCommand({ type: 'move', direction: 'backward', speed })
    } else if (direction === 'left') {
      onSendCommand({ type: 'move', direction: 'left', speed })
    } else if (direction === 'right') {
      onSendCommand({ type: 'move', direction: 'right', speed })
    }

    // Clear click target and return to AI mode after a delay
    if (manualCommandTimeoutRef.current) {
      clearTimeout(manualCommandTimeoutRef.current)
    }

    // Stop after 800ms and return to AI control
    manualCommandTimeoutRef.current = setTimeout(() => {
      onSendCommand({ type: 'move', direction: 'stop', speed: 0 })
      setClickTarget(null)
      setIsManualMode(false)
    }, 800)
  }, [connected, onSendCommand])

  // Clear click target after animation
  useEffect(() => {
    if (clickTarget) {
      const timer = setTimeout(() => {
        setClickTarget(null)
      }, 1500)
      return () => clearTimeout(timer)
    }
  }, [clickTarget])

  // Get action icon
  const getActionIcon = (action) => {
    switch (action) {
      case 'forward':
      case 'slow_forward':
        return <ArrowUp size={16} />
      case 'backup':
        return <ArrowDown size={16} />
      case 'turn_left':
        return <ArrowLeft size={16} />
      case 'turn_right':
        return <ArrowRight size={16} />
      default:
        return <Eye size={16} />
    }
  }

  // Format log entry
  const formatLogEntry = (entry) => {
    const levelColors = {
      info: '#00ff80',
      warning: '#ffaa00',
      danger: '#ff4444',
      action: '#00aaff'
    }
    return {
      color: levelColors[entry.level] || '#888',
      icon: entry.level === 'danger' ? '🚨' :
            entry.level === 'warning' ? '⚠️' :
            entry.level === 'action' ? '🎯' : '📊'
    }
  }

  return (
    <div className="ai-mode-view">
      <div className="ai-main-content">
        {/* Camera feeds */}
        <div className="ai-camera-grid">
          {/* Original Camera Feed - Clickable for navigation */}
          <div
            className={`camera-panel clickable-feed ${isManualMode ? 'manual-mode' : ''}`}
            onClick={handleVideoClick}
            ref={liveFeedRef}
          >
            <div className="camera-label">
              <MousePointer size={14} style={{ marginRight: '6px' }} />
              Live Feed - Click to Navigate
            </div>
            <VideoView
              frame={videoFrame}
              connected={connected}
              sensorData={sensorData}
              settings={settings}
              showOverlays={false}
            />

            {/* Click target indicator */}
            {clickTarget && (
              <div
                className="click-target"
                style={{
                  left: clickTarget.x,
                  top: clickTarget.y
                }}
              >
                <Target size={40} className="target-icon" />
                <div className="click-direction">
                  {clickTarget.relX < 0.33 ? 'LEFT' :
                   clickTarget.relX > 0.67 ? 'RIGHT' :
                   clickTarget.relY < 0.4 ? 'FORWARD' :
                   clickTarget.relY > 0.7 ? 'BACK' : 'FORWARD'}
                </div>
              </div>
            )}

            {/* Navigation zones overlay hint */}
            <div className="nav-zones-hint">
              <div className="zone-hint left">
                <ArrowLeft size={24} />
              </div>
              <div className="zone-hint center">
                <ArrowUp size={24} />
              </div>
              <div className="zone-hint right">
                <ArrowRight size={24} />
              </div>
            </div>

            {/* Manual mode indicator */}
            {isManualMode && (
              <div className="manual-mode-indicator">
                <MousePointer size={16} />
                <span>Manual Override</span>
              </div>
            )}
          </div>

          {/* AI Processed Feed */}
          <div className="camera-panel ai-vision-panel">
            <div className="camera-label">
              <Eye size={14} style={{ marginRight: '6px' }} />
              AI Vision
            </div>
            {aiError && (
              <div className="ai-error">
                <AlertCircle size={20} />
                <span>AI Service Error: {aiError}</span>
              </div>
            )}
            {processedFrame ? (
              <img
                src={processedFrame}
                alt="AI Processed Camera Feed"
                className="video-frame-processed"
              />
            ) : videoFrame ? (
              <img
                src={videoFrame}
                alt="Camera Feed"
                className="video-frame-processed"
              />
            ) : (
              <div className="ai-placeholder">
                <div>Waiting for video feed...</div>
              </div>
            )}

            {/* Obstacle Detection Overlay - Always show when we have data */}
            <div className="obstacle-overlay">
              <div className="zone-indicators">
                <div className={`zone-box left ${obstacleData?.left_clear !== false ? 'clear' : 'blocked'}`}>
                  L {obstacleData?.left_clear !== false ? '✓' : '✗'}
                </div>
                <div className={`zone-box center ${obstacleData?.center_blocked !== true ? 'clear' : 'blocked'}`}>
                  C {obstacleData?.center_blocked !== true ? '✓' : '✗'}
                </div>
                <div className={`zone-box right ${obstacleData?.right_clear !== false ? 'clear' : 'blocked'}`}>
                  R {obstacleData?.right_clear !== false ? '✓' : '✗'}
                </div>
              </div>
            </div>

            {/* Action indicator */}
            {navigationCommand && (
              <div className="action-indicator-overlay">
                <div className={`action-badge ${navigationCommand.action || 'stop'}`}>
                  {getActionIcon(navigationCommand.action)}
                  <span>{(navigationCommand.action || 'STOP').toUpperCase().replace('_', ' ')}</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right sidebar with chat and controls */}
        <div className="ai-sidebar">
          {/* AI Companion Chat Panel */}
          <div className="ai-companion-panel expanded">
            <div className="companion-header">
              <Bot size={18} />
              <span>AI Companion</span>
              <div className={`companion-status ${isAutonomousRunning ? 'running' : connected ? 'active' : 'inactive'}`}>
                {isAutonomousRunning ? 'Exploring' : connected ? 'Ready' : 'Offline'}
              </div>
            </div>

            {/* Chat messages */}
            <div className="companion-chat" ref={chatContainerRef}>
              {chatMessages.map((msg, idx) => (
                <div key={msg.timestamp + idx} className={`chat-bubble ${msg.role} ${idx === chatMessages.length - 1 ? 'latest' : ''}`}>
                  {msg.role === 'assistant' && (
                    <div className="chat-avatar">
                      <Bot size={14} />
                    </div>
                  )}
                  <div className={`chat-content ${msg.role}`}>
                    <p>{msg.text}</p>
                  </div>
                </div>
              ))}
            </div>

            {/* Command input */}
            <div className="chat-input-container">
              <input
                ref={inputRef}
                type="text"
                className="chat-input"
                placeholder={connected ? "Type a command..." : "Connect to robot first"}
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                onKeyPress={handleKeyPress}
                disabled={!connected}
              />
              <button
                className="chat-send-btn"
                onClick={handleSendCommand}
                disabled={!connected || !userInput.trim()}
              >
                <Send size={18} />
              </button>
            </div>

            {/* Quick action buttons */}
            <div className="quick-actions">
              <button
                className={`quick-action-btn ${isAutonomousRunning ? 'stop' : 'start'}`}
                onClick={() => {
                  if (isAutonomousRunning) {
                    setIsAutonomousRunning(false)
                    if (onSendCommand) onSendCommand({ type: 'move', direction: 'stop', speed: 0 })
                    setChatMessages(prev => [...prev, { role: 'assistant', text: "Stopping. Awaiting your next command.", timestamp: Date.now() }])
                  } else {
                    setIsAutonomousRunning(true)
                    setChatMessages(prev => [...prev, { role: 'assistant', text: "Starting autonomous exploration!", timestamp: Date.now() }])
                  }
                }}
                disabled={!connected}
              >
                {isAutonomousRunning ? <Square size={14} /> : <Play size={14} />}
                <span>{isAutonomousRunning ? 'Stop' : 'Start Exploring'}</span>
              </button>
            </div>

            {/* Detected objects summary */}
            {detectedObjects.length > 0 && (
              <div className="detected-objects-bar">
                <Eye size={12} />
                <span>Seeing: {detectedObjects.map(o => o.type).join(', ')}</span>
              </div>
            )}
          </div>

          {/* Compact Radar View */}
          <RadarView
            radarData={radarData}
            sensorData={sensorData}
            navigationState={navigationState}
            dangerZone={dangerZone}
          />
        </div>
      </div>

      {/* Bottom status bar */}
      <div className="ai-status-bar">
        <div className="status-item">
          <span className="status-label">STATE</span>
          <span className={`status-value state-${navigationState || 'idle'}`}>
            {navigationState?.toUpperCase().replace('_', ' ') || 'IDLE'}
          </span>
        </div>
        <div className="status-item">
          <span className="status-label">ACTION</span>
          <span className={`status-value action-${navigationCommand?.action || 'stop'}`}>
            {(navigationCommand?.action || 'STOP').toUpperCase().replace('_', ' ')}
          </span>
        </div>
        <div className="status-item">
          <span className="status-label">FRONT</span>
          <span className={`status-value dist-${dangerZone}`}>
            {Math.round(radarData?.ultrasonic_distance || sensorData?.distance || 0)}cm
          </span>
        </div>
        <div className="status-item">
          <span className="status-label">BACK</span>
          <span className={`status-value dist-${(radarData?.ultrasonic_distance_back || sensorData?.distanceBack || 100) < 20 ? 'danger' : (radarData?.ultrasonic_distance_back || sensorData?.distanceBack || 100) < 40 ? 'caution' : 'clear'}`}>
            {Math.round(radarData?.ultrasonic_distance_back || sensorData?.distanceBack || 0)}cm
          </span>
        </div>
        <div className="status-item">
          <span className="status-label">FRAME Δ</span>
          <span className="status-value">
            {navigationCommand?.frame_change?.toFixed(1) || '0.0'}
          </span>
        </div>
        {navigationCommand?.is_stuck && (
          <div className="status-item stuck">
            <span className="status-label">STATUS</span>
            <span className="status-value">STUCK - RECOVERING</span>
          </div>
        )}
      </div>
    </div>
  )
}
