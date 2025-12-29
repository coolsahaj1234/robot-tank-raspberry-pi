import { useState, useEffect, useRef, useCallback } from 'react'

const getAiServiceUrl = () => {
  const host = window.location.hostname
  return `http://${host}:5001`
}

const AI_SERVICE_URL = getAiServiceUrl()

/**
 * Hook for AI video processing with reactive navigation
 * Sends frames to Python AI service and receives:
 * - Processed frames with obstacle detection
 * - Navigation commands (speed, turn, LEDs)
 * - Radar data (position, path history, obstacles)
 */
export function useAIVideoProcessor(videoFrame, enabled, sensorData = null, isSantaMode = false, isSantaStandby = false, isAutoParkMode = false) {
  const [processedFrame, setProcessedFrame] = useState(null)
  const [laneData, setLaneData] = useState(null)
  const [obstacleData, setObstacleData] = useState(null)
  const [navigationCommand, setNavigationCommand] = useState(null)
  const [radarData, setRadarData] = useState(null)
  const [navigationState, setNavigationState] = useState('idle')
  const [thinkingLog, setThinkingLog] = useState([])
  const [narration, setNarration] = useState('')
  const [detectedObjects, setDetectedObjects] = useState([])
  const [processing, setProcessing] = useState(false)
  const [error, setError] = useState(null)

  const processingRef = useRef(false)
  const frameCountRef = useRef(0)

  const processFrame = useCallback(async (frame) => {
    if (!frame || processingRef.current) {
      return
    }

    processingRef.current = true
    setProcessing(true)

    try {
      const base64Data = frame.includes(',') ? frame.split(',')[1] : frame

      const requestBody = {
        frame: base64Data,
        santa_mode: isSantaMode,
        santa_standby: isSantaStandby,
        auto_park_mode: isAutoParkMode
      }

      // Add front ultrasonic distance
      if (sensorData?.distance !== null && sensorData?.distance !== undefined) {
        requestBody.ultrasonic_distance = sensorData.distance
      }

      // Add back ultrasonic distance
      if (sensorData?.distanceBack !== null && sensorData?.distanceBack !== undefined) {
        requestBody.ultrasonic_distance_back = sensorData.distanceBack
      }

      const response = await fetch(`${AI_SERVICE_URL}/process_frame`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      })

      if (!response.ok) {
        throw new Error(`AI service error: ${response.statusText}`)
      }

      const result = await response.json()

      // Update state with processed data
      if (result.processed_frame) {
        setProcessedFrame(`data:image/jpeg;base64,${result.processed_frame}`)
      }

      if (result.lane_data) {
        setLaneData(result.lane_data)
      }

      if (result.obstacle_data) {
        setObstacleData(result.obstacle_data)
      }

      if (result.navigation_command) {
        setNavigationCommand(result.navigation_command)
      }

      // New: Radar and navigation state data
      if (result.radar_data) {
        setRadarData(result.radar_data)
      }

      if (result.navigation_state) {
        setNavigationState(result.navigation_state)
      }

      // AI thinking log
      if (result.thinking_log) {
        setThinkingLog(result.thinking_log)
      }

      // Natural language narration
      if (result.narration) {
        setNarration(result.narration)
      }

      // Detected objects
      if (result.detected_objects) {
        setDetectedObjects(result.detected_objects)
      }

      setError(null)
    } catch (err) {
      console.error('AI processing error:', err)
      setError(err.message)
    } finally {
      processingRef.current = false
      setProcessing(false)
    }
  }, [sensorData, isSantaMode, isSantaStandby, isAutoParkMode])

  // Process frames when enabled
  useEffect(() => {
    if (!enabled || !videoFrame) {
      setProcessedFrame(null)
      setLaneData(null)
      setObstacleData(null)
      setNavigationCommand(null)
      setRadarData(null)
      setNavigationState('idle')
      setThinkingLog([])
      return
    }

    // Process every 2nd frame for better responsiveness
    frameCountRef.current++
    if (frameCountRef.current % 2 === 0) {
      processFrame(videoFrame)
    }
  }, [videoFrame, enabled, processFrame])

  return {
    processedFrame,
    laneData,
    obstacleData,
    navigationCommand,
    radarData,
    navigationState,
    thinkingLog,
    narration,
    detectedObjects,
    processing,
    error
  }
}
