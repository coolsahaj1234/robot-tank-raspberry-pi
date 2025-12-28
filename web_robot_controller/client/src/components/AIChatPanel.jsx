import React, { useState, useEffect, useRef, useCallback } from 'react'
<<<<<<< HEAD
import { Bot, Send, Play, Square } from 'lucide-react'
=======
import { Bot, Send, Play, Square, Camera, Eye, EyeOff } from 'lucide-react'
>>>>>>> 40885bf (Initial commit)
import './AIChatPanel.css'

/**
 * AIChatPanel - Conversational interface for AI mode
 * User can chat with the robot, give commands, and control autonomous navigation
 */
export default function AIChatPanel({
  connected,
  sensorData,
  radarData,
  detectedObjects = [],
  navigationCommand,
  narration,
  autonomousEnabled,
  onSetAutonomousEnabled,
<<<<<<< HEAD
  onSendCommand,
  dangerZone
=======
  isSantaMode,
  isSantaStandby,
  onSetSantaStandby,
  onSendCommand,
  dangerZone,
  videoFrame
>>>>>>> 40885bf (Initial commit)
}) {
  const chatContainerRef = useRef(null)
  const inputRef = useRef(null)
  const lastNarrationRef = useRef('')
  const lastNarrationTimeRef = useRef(0)

  const [chatMessages, setChatMessages] = useState([
    {
      role: 'assistant',
      text: "Hello! I'm your AI companion. Say 'start exploring' to begin autonomous navigation, or give me commands like 'turn left' or 'move forward'.",
      timestamp: Date.now()
    }
  ])
  const [userInput, setUserInput] = useState('')

  // Throttle narration - only add message every 3 seconds minimum
  const NARRATION_THROTTLE_MS = 3000

  // Add AI narration to chat when autonomous mode is running (throttled)
  useEffect(() => {
    if (!narration || !autonomousEnabled || narration.length < 5) return
    if (narration === lastNarrationRef.current) return

    const now = Date.now()
    if (now - lastNarrationTimeRef.current < NARRATION_THROTTLE_MS) return

    lastNarrationRef.current = narration
    lastNarrationTimeRef.current = now
    setChatMessages(prev => [...prev, { role: 'assistant', text: narration, timestamp: now }].slice(-15))
  }, [narration, autonomousEnabled])

  // Auto-scroll chat
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight
    }
  }, [chatMessages])

  // Handle user command
  const handleSendCommand = useCallback(() => {
    if (!userInput.trim() || !connected) return

    const command = userInput.trim().toLowerCase()
    setChatMessages(prev => [...prev, { role: 'user', text: userInput.trim(), timestamp: Date.now() }].slice(-25))
    setUserInput('')

    let response = ''

    // Start/Stop autonomous navigation
    if (command.includes('start') || command.includes('explore') || (command.includes('go') && command.includes('auto'))) {
      onSetAutonomousEnabled(true)
      response = "Starting autonomous exploration! I'll navigate and tell you what I see. Say 'stop' anytime."
    }
    else if (command.includes('stop') || command.includes('halt') || command.includes('pause')) {
      onSetAutonomousEnabled(false)
      if (onSendCommand) onSendCommand({ type: 'move', direction: 'stop', speed: 0 })
      response = "Stopping. Awaiting your command."
    }
    // Direct movement
    else if (command.includes('forward') || command.includes('ahead') || command.includes('straight')) {
      if (onSendCommand) {
        onSendCommand({ type: 'move', direction: 'forward', speed: 50 })
        setTimeout(() => onSendCommand({ type: 'move', direction: 'stop', speed: 0 }), 1000)
      }
      response = "Moving forward..."
    }
    else if (command.includes('back') || command.includes('reverse')) {
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
      response = `I can see ${objects}. The nearest obstacle is about ${Math.round(distance)}cm away.`
    }
    else if (command.includes('status') || command.includes('how are you')) {
      const frontDist = sensorData?.distance || radarData?.ultrasonic_distance || 0
      const backDist = sensorData?.distanceBack || radarData?.ultrasonic_distance_back || 0
      response = `I'm ${autonomousEnabled ? 'exploring autonomously' : 'waiting for commands'}. Front: ${Math.round(frontDist)}cm, Back: ${Math.round(backDist)}cm. ${dangerZone === 'danger' ? 'Warning: obstacle very close!' : dangerZone === 'caution' ? 'Something nearby.' : 'Path looks clear.'}`
    }
    else if (command.includes('help') || command.includes('commands')) {
      response = "Commands: 'start exploring', 'stop', 'turn left/right', 'move forward/back', 'what do you see?', 'status'"
    }
    else {
      response = `Not sure about "${userInput.trim()}". Try 'start exploring', 'stop', 'turn left', or 'what do you see?'`
    }

    setTimeout(() => {
      setChatMessages(prev => [...prev, { role: 'assistant', text: response, timestamp: Date.now() }].slice(-25))
    }, 300)
  }, [userInput, connected, onSendCommand, onSetAutonomousEnabled, sensorData, radarData, detectedObjects, dangerZone, autonomousEnabled])

<<<<<<< HEAD
=======
  const handleCapturePhoto = useCallback(async () => {
    if (!videoFrame || !connected) return

    try {
      const base64Data = videoFrame.includes(',') ? videoFrame.split(',')[1] : videoFrame
      const host = window.location.hostname
      const aiServiceUrl = `http://${host}:5001`

      const response = await fetch(`${aiServiceUrl}/capture_photo`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ frame: base64Data })
      })

      if (response.ok) {
        const result = await response.json()
        setChatMessages(prev => [...prev, {
          role: 'assistant',
          text: `📸 Photo captured! Saved as ${result.filename}`,
          timestamp: Date.now()
        }])
      } else {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
        console.error('Capture failed:', errorData)
        setChatMessages(prev => [...prev, {
          role: 'assistant',
          text: `❌ Failed to capture photo: ${errorData.error || response.statusText}`,
          timestamp: Date.now()
        }])
      }
    } catch (error) {
      console.error('Photo capture error:', error)
      setChatMessages(prev => [...prev, {
        role: 'assistant',
        text: `❌ Error capturing photo: ${error.message}`,
        timestamp: Date.now()
      }])
    }
  }, [videoFrame, connected])

>>>>>>> 40885bf (Initial commit)
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendCommand()
    }
  }

  return (
    <div className="ai-chat-panel">
      <div className="chat-header">
        <Bot size={20} />
        <span>AI Companion</span>
        <div className={`chat-status ${autonomousEnabled ? 'exploring' : connected ? 'ready' : 'offline'}`}>
          {autonomousEnabled ? 'Exploring' : connected ? 'Ready' : 'Offline'}
        </div>
      </div>

      <div className="chat-messages" ref={chatContainerRef}>
        {chatMessages.map((msg, idx) => (
          <div key={msg.timestamp + idx} className={`message ${msg.role}`}>
            {msg.role === 'assistant' && (
              <div className="message-avatar">
                <Bot size={14} />
              </div>
            )}
            <div className="message-content">
              <p>{msg.text}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="chat-input-area">
        <input
          ref={inputRef}
          type="text"
          placeholder={connected ? "Type a command..." : "Connect first"}
          value={userInput}
          onChange={(e) => setUserInput(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={!connected}
        />
        <button
          className="send-btn"
          onClick={handleSendCommand}
          disabled={!connected || !userInput.trim()}
        >
          <Send size={18} />
        </button>
      </div>

      <div className="chat-actions">
        <button
          className={`action-btn ${autonomousEnabled ? 'stop' : 'start'}`}
          onClick={() => {
            if (autonomousEnabled) {
              onSetAutonomousEnabled(false)
              if (onSendCommand) onSendCommand({ type: 'move', direction: 'stop', speed: 0 })
              setChatMessages(prev => [...prev, { role: 'assistant', text: "Stopping. Ready for commands.", timestamp: Date.now() }])
            } else {
              onSetAutonomousEnabled(true)
              setChatMessages(prev => [...prev, { role: 'assistant', text: "Starting autonomous exploration!", timestamp: Date.now() }])
            }
          }}
          disabled={!connected}
        >
          {autonomousEnabled ? <Square size={14} /> : <Play size={14} />}
          <span>{autonomousEnabled ? 'Stop' : 'Start Exploring'}</span>
        </button>
<<<<<<< HEAD
=======

        {isSantaMode && (
          <button
            className={`action-btn standby ${isSantaStandby ? 'active' : ''}`}
            onClick={() => {
              const newStandby = !isSantaStandby
              onSetSantaStandby(newStandby)
              setChatMessages(prev => [...prev, {
                role: 'assistant',
                text: newStandby
                  ? "Standby Mode Active. I'll stay here and watch for Santa! 🎅📸"
                  : "Standby Mode deactivated. I'll move around again.",
                timestamp: Date.now()
              }])
            }}
            disabled={!connected}
            title="Santa Standby: Track people/hats from here and take photos."
          >
            {isSantaStandby ? <Camera size={14} /> : <Eye size={14} />}
            <span>{isSantaStandby ? 'Standby ON' : 'Santa Standby'}</span>
          </button>
        )}

        {isSantaMode && isSantaStandby && (
          <button
            className="action-btn capture"
            onClick={handleCapturePhoto}
            disabled={!connected || !videoFrame}
            title="Manually capture and save a photo"
          >
            <Camera size={14} />
            <span>Capture Photo</span>
          </button>
        )}
>>>>>>> 40885bf (Initial commit)
      </div>

    </div>
  )
}
