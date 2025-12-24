import { useState, useEffect, useRef, useCallback } from 'react'

const WS_URL = 'ws://localhost:3002'
const DEFAULT_IP = '10.0.0.86'
const DEFAULT_COMMAND_PORT = 5003
const DEFAULT_VIDEO_PORT = 8003

export function useRobotConnection() {
  const [connected, setConnected] = useState(false)
  const [connecting, setConnecting] = useState(false)
  const [videoFrame, setVideoFrame] = useState(null)
  const [sensorData, setSensorData] = useState({
    distance: null,  // Front distance
    distanceBack: null,  // Back distance
    infrared: null
  })
  
  const wsRef = useRef(null)
  const settingsRef = useRef({
    ip: localStorage.getItem('robotIP') || DEFAULT_IP,
    commandPort: parseInt(localStorage.getItem('commandPort') || DEFAULT_COMMAND_PORT),
    videoPort: parseInt(localStorage.getItem('videoPort') || DEFAULT_VIDEO_PORT)
  })

  const connect = useCallback((ip, commandPort, videoPort) => {
    if (connecting || connected) return
    
    setConnecting(true)
    
    // Save settings
    settingsRef.current = { ip, commandPort, videoPort }
    localStorage.setItem('robotIP', ip)
    localStorage.setItem('commandPort', commandPort.toString())
    localStorage.setItem('videoPort', videoPort.toString())
    
    // Connect WebSocket
    const ws = new WebSocket(WS_URL)
    
    ws.onopen = () => {
      console.log('WebSocket connected')
      ws.send(JSON.stringify({
        type: 'connect',
        ip,
        commandPort,
        videoPort
      }))
    }
    
    ws.onmessage = (event) => {
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
          
        case 'video_frame':
          // Convert base64 to image URL
          try {
            const imageUrl = `data:image/jpeg;base64,${data.data}`
            setVideoFrame(imageUrl)
            // Log every 30th frame to avoid spam
            if (Math.random() < 0.033) {
              console.log(`📹 Received video frame (${data.length} bytes)`)
            }
          } catch (error) {
            console.error('Error processing video frame:', error)
          }
          break
          
        case 'command_response':
          // Parse sensor data from responses like "CMD_SONIC#123#456" (front#back)
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
    }
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      setConnecting(false)
    }
    
    ws.onclose = () => {
      console.log('WebSocket closed')
      setConnected(false)
      setConnecting(false)
    }
    
    wsRef.current = ws
  }, [connecting, connected])

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.send(JSON.stringify({ type: 'disconnect' }))
      wsRef.current.close()
      wsRef.current = null
    }
    setConnected(false)
    setConnecting(false)
    setVideoFrame(null)
  }, [])

  const sendCommand = useCallback((command) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'command',
        command
      }))
      console.log(`📤 Command sent: ${command}`)
    } else {
      console.warn('⚠️ WebSocket not connected, cannot send command:', command)
    }
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

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

