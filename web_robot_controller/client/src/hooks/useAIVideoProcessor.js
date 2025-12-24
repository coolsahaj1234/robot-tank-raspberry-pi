import { useState, useEffect, useRef, useCallback } from 'react'

const AI_SERVICE_URL = 'http://localhost:5000'

/**
 * Hook for AI video processing
 * Sends frames to Python AI service and receives processed frames + navigation commands
 */
export function useAIVideoProcessor(videoFrame, enabled) {
  const [processedFrame, setProcessedFrame] = useState(null)
  const [laneData, setLaneData] = useState(null)
  const [obstacleData, setObstacleData] = useState(null)
  const [navigationCommand, setNavigationCommand] = useState(null)
  const [processing, setProcessing] = useState(false)
  const [error, setError] = useState(null)
  
  const processingRef = useRef(false)
  const frameQueueRef = useRef([])
  
  const processFrame = useCallback(async (frame) => {
    if (!frame || processingRef.current) {
      return
    }
    
    processingRef.current = true
    setProcessing(true)
    
    try {
      // Extract base64 from data URL
      const base64Data = frame.includes(',') ? frame.split(',')[1] : frame
      
      const response = await fetch(`${AI_SERVICE_URL}/process_frame`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          frame: base64Data
        })
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
      
      setError(null)
    } catch (err) {
      console.error('AI processing error:', err)
      setError(err.message)
    } finally {
      setProcessing(false)
      processingRef.current = false
    }
  }, [])
  
  // Process frames when enabled
  useEffect(() => {
    if (!enabled || !videoFrame) {
      setProcessedFrame(null)
      setLaneData(null)
      setObstacleData(null)
      setNavigationCommand(null)
      return
    }
    
    // Throttle processing (process every 3rd frame to avoid overload)
    const frameCount = frameQueueRef.current.length
    frameQueueRef.current.push(videoFrame)
    
    if (frameCount % 3 === 0) {
      const frameToProcess = frameQueueRef.current.shift()
      if (frameToProcess) {
        processFrame(frameToProcess)
      }
    }
  }, [videoFrame, enabled, processFrame])
  
  return {
    processedFrame,
    laneData,
    obstacleData,
    navigationCommand,
    processing,
    error
  }
}

