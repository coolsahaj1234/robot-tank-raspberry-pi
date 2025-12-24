import { useState, useEffect, useRef, useCallback } from 'react'

// Dynamic WebSocket URL - uses current host for LAN access
const getWsUrl = () => {
  const host = window.location.hostname
  return `ws://${host}:3002`
}

const DEFAULT_IP = '10.0.0.86'
const DEFAULT_COMMAND_PORT = 5003
const DEFAULT_VIDEO_PORT = 8003

// Connection settings
const HEARTBEAT_INTERVAL = 15000    // Send ping every 15 seconds
const RECONNECT_DELAY = 2000        // Wait 2 seconds before reconnecting
const MAX_RECONNECT_ATTEMPTS = 10   // Max reconnection attempts

export function useRobotConnection() {
  const [connected, setConnected] = useState(false)
  const [connecting, setConnecting] = useState(false)
  const [videoFrame, setVideoFrame] = useState(null)
  const [sensorData, setSensorData] = useState({
    distance: null,
    distanceBack: null,
    infrared: null
  })

  const wsRef = useRef(null)
  const heartbeatRef = useRef(null)
  const reconnectTimeoutRef = useRef(null)
  const reconnectAttemptsRef = useRef(0)
  const shouldReconnectRef = useRef(false)
  const lastPongRef = useRef(Date.now())

  const settingsRef = useRef({
    ip: localStorage.getItem('robotIP') || DEFAULT_IP,
    commandPort: parseInt(localStorage.getItem('commandPort') || DEFAULT_COMMAND_PORT),
    videoPort: parseInt(localStorage.getItem('videoPort') || DEFAULT_VIDEO_PORT)
  })

  // Clear all timers
  const clearTimers = useCallback(() => {
    if (heartbeatRef.current) {
      clearInterval(heartbeatRef.current)
      heartbeatRef.current = null
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
  }, [])

  // Start heartbeat to keep connection alive
  const startHeartbeat = useCallback(() => {
    clearTimers()
    lastPongRef.current = Date.now()

    heartbeatRef.current = setInterval(() => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        // Send ping
        wsRef.current.send(JSON.stringify({ type: 'ping' }))

        // Check if we got a pong recently (within 30 seconds)
        const timeSinceLastPong = Date.now() - lastPongRef.current
        if (timeSinceLastPong > 30000) {
          console.warn('⚠️ No pong received for 30s, connection may be stale')
          // Force reconnection
          if (wsRef.current) {
            wsRef.current.close()
          }
        }
      }
    }, HEARTBEAT_INTERVAL)
  }, [clearTimers])

  // Internal connect function
  const connectInternal = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      return
    }

    const wsUrl = getWsUrl()
    console.log(`🔌 Connecting to WebSocket: ${wsUrl}`)

    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      console.log('✅ WebSocket connected')
      reconnectAttemptsRef.current = 0

      // Send connect command to bridge
      const { ip, commandPort, videoPort } = settingsRef.current
      ws.send(JSON.stringify({
        type: 'connect',
        ip,
        commandPort,
        videoPort
      }))

      // Start heartbeat
      startHeartbeat()
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)

        switch (data.type) {
          case 'connected':
            setConnected(true)
            setConnecting(false)
            console.log('✅ Connected to robot')
            break

          case 'disconnected':
            setConnected(false)
            setConnecting(false)
            console.log('❌ Disconnected from robot')
            break

          case 'connection_failed':
            // Robot connection failed but WebSocket is still open
            // This allows retry without full reconnection
            setConnected(false)
            setConnecting(false)
            console.error('❌ Robot connection failed:', data.message)
            // Don't trigger WebSocket reconnect - just let user retry
            break

          case 'pong':
            // Update last pong time
            lastPongRef.current = Date.now()
            break

          case 'video_frame':
            try {
              const imageUrl = `data:image/jpeg;base64,${data.data}`
              setVideoFrame(imageUrl)
            } catch (error) {
              console.error('Error processing video frame:', error)
            }
            break

          case 'command_response':
            const response = data.data.trim()
            if (response.startsWith('CMD_SONIC#')) {
              const parts = response.split('#')
              if (parts.length >= 2) {
                const distanceFront = parseFloat(parts[1])
                const distanceBack = parts.length >= 3 ? parseFloat(parts[2]) : null
                setSensorData(prev => ({
                  ...prev,
                  distance: distanceFront,
                  distanceBack: distanceBack
                }))
              }
            }
            break

          case 'error':
            console.error('Robot error:', data.message)
            setConnecting(false)
            break

          case 'ready':
            console.log('WebSocket ready')
            break
        }
      } catch (e) {
        // Ignore non-JSON messages
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      setConnecting(false)
    }

    ws.onclose = (event) => {
      console.log(`WebSocket closed (code: ${event.code}, reason: ${event.reason})`)
      setConnected(false)
      setConnecting(false)
      clearTimers()

      // Auto-reconnect if we should
      if (shouldReconnectRef.current && reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
        reconnectAttemptsRef.current++
        console.log(`🔄 Reconnecting in ${RECONNECT_DELAY}ms (attempt ${reconnectAttemptsRef.current}/${MAX_RECONNECT_ATTEMPTS})...`)

        reconnectTimeoutRef.current = setTimeout(() => {
          setConnecting(true)
          connectInternal()
        }, RECONNECT_DELAY)
      } else if (reconnectAttemptsRef.current >= MAX_RECONNECT_ATTEMPTS) {
        console.error('❌ Max reconnection attempts reached')
        shouldReconnectRef.current = false
      }
    }

    wsRef.current = ws
  }, [clearTimers, startHeartbeat])

  const connect = useCallback((ip, commandPort, videoPort) => {
    // Allow reconnect if not currently connecting
    if (connecting) return

    setConnecting(true)
    setConnected(false)
    shouldReconnectRef.current = true
    reconnectAttemptsRef.current = 0

    // Save settings
    settingsRef.current = { ip, commandPort, videoPort }
    localStorage.setItem('robotIP', ip)
    localStorage.setItem('commandPort', commandPort.toString())
    localStorage.setItem('videoPort', videoPort.toString())

    // If WebSocket already open, just send connect command
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'connect',
        ip,
        commandPort,
        videoPort
      }))
    } else {
      connectInternal()
    }
  }, [connecting, connectInternal])

  const disconnect = useCallback(() => {
    shouldReconnectRef.current = false
    clearTimers()

    if (wsRef.current) {
      wsRef.current.send(JSON.stringify({ type: 'disconnect' }))
      wsRef.current.close()
      wsRef.current = null
    }
    setConnected(false)
    setConnecting(false)
    setVideoFrame(null)
  }, [clearTimers])

  const sendCommand = useCallback((command) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'command',
        command
      }))
    } else {
      console.warn('⚠️ WebSocket not connected, cannot send command:', command)
    }
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      shouldReconnectRef.current = false
      clearTimers()
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [clearTimers])

  return {
    connected,
    connecting,
    connect,
    disconnect,
    sendCommand,
    videoFrame,
    sensorData,
    settings: settingsRef.current
  }
}
