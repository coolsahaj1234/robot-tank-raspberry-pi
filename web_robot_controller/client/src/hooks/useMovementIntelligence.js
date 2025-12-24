import { useState, useEffect, useRef, useCallback } from 'react'

/**
 * Intelligent movement control hook
 * - Starts at 50% speed in Move mode
 * - Uses camera feed to detect if robot is stuck
 * - Uses sensor data to avoid obstacles
 * - Gradually increases speed when safe
 */
export function useMovementIntelligence({
  connected,
  videoFrame,
  sensorData,
  currentMode,
  baseSpeed,
  onSendCommand
}) {
  const [effectiveSpeed, setEffectiveSpeed] = useState(50) // Start at 50%
  const [isStuck, setIsStuck] = useState(false)
  const [obstacleDetected, setObstacleDetected] = useState(false)
  
  const previousFrameRef = useRef(null)
  const frameChangeCountRef = useRef(0)
  const stuckCheckIntervalRef = useRef(null)
  const speedIncreaseIntervalRef = useRef(null)
  const lastMovementTimeRef = useRef(Date.now())

  // Detect if robot is stuck by analyzing camera frames
  useEffect(() => {
    if (!connected || !videoFrame || currentMode !== '1') {
      setIsStuck(false)
      frameChangeCountRef.current = 0
      previousFrameRef.current = null
      if (stuckCheckIntervalRef.current) {
        clearInterval(stuckCheckIntervalRef.current)
        stuckCheckIntervalRef.current = null
      }
      return
    }

    // Simple frame difference detection
    // Track frame changes - if frames don't change, robot might be stuck
    if (previousFrameRef.current !== videoFrame) {
      // Frame changed - robot is moving
      frameChangeCountRef.current = 0
      setIsStuck(false)
      lastMovementTimeRef.current = Date.now()
    } else {
      // Same frame - increment counter
      frameChangeCountRef.current++
    }

    // Check if stuck (same frame for too long)
    const checkStuck = () => {
      const timeSinceLastMovement = Date.now() - lastMovementTimeRef.current
      if (frameChangeCountRef.current > 5 && timeSinceLastMovement > 3000) {
        // Same frame for 5+ checks and 3+ seconds = likely stuck
        setIsStuck(true)
        console.log('⚠️ Robot appears stuck - reducing speed')
      } else if (frameChangeCountRef.current <= 2) {
        setIsStuck(false)
      }
    }

    const interval = setInterval(checkStuck, 1000) // Check every second
    stuckCheckIntervalRef.current = interval
    
    previousFrameRef.current = videoFrame

    return () => {
      if (interval) clearInterval(interval)
    }
  }, [connected, videoFrame, currentMode])

  // Monitor sensor data for obstacles
  useEffect(() => {
    if (!connected || currentMode !== '1') {
      setObstacleDetected(false)
      return
    }

    const frontDistance = sensorData.distance
    const rearDistance = sensorData.distanceBack

    // Detect obstacles
    if (frontDistance !== null && frontDistance < 30) {
      setObstacleDetected(true)
      console.log(`⚠️ Obstacle detected: ${frontDistance.toFixed(1)}cm ahead`)
    } else if (rearDistance !== null && rearDistance < 30) {
      setObstacleDetected(true)
      console.log(`⚠️ Obstacle detected: ${rearDistance.toFixed(1)}cm behind`)
    } else {
      setObstacleDetected(false)
    }
  }, [connected, sensorData, currentMode])

  // Adjust effective speed based on conditions
  useEffect(() => {
    if (!connected || currentMode !== '1') {
      setEffectiveSpeed(baseSpeed)
      return
    }

    setEffectiveSpeed(prev => {
      let targetSpeed = prev

      // Initialize to 50% of base speed when entering Move mode
      if (prev === baseSpeed && baseSpeed > 50) {
        targetSpeed = Math.max(50, Math.round(baseSpeed * 0.5))
        console.log(`🚀 Move mode: Starting at ${targetSpeed}% (50% of ${baseSpeed}%)`)
        return targetSpeed
      }

      // Reduce speed if stuck
      if (isStuck) {
        targetSpeed = Math.max(20, Math.round(prev * 0.5))
        if (targetSpeed !== prev) {
          console.log('🐌 Reducing speed due to stuck detection')
        }
        return targetSpeed
      }

      // Reduce speed if obstacle detected
      if (obstacleDetected) {
        const frontDistance = sensorData.distance || 100
        const rearDistance = sensorData.distanceBack || 100
        const minDistance = Math.min(frontDistance, rearDistance)
        
        // Gradually reduce speed as obstacle gets closer
        if (minDistance < 30) {
          const speedMultiplier = Math.max(0.3, minDistance / 30)
          targetSpeed = Math.max(20, Math.round(prev * speedMultiplier))
          if (targetSpeed !== prev) {
            console.log(`🚧 Reducing speed due to obstacle: ${minDistance.toFixed(1)}cm`)
          }
          return targetSpeed
        }
      }

      return prev
    })
  }, [connected, currentMode, baseSpeed, isStuck, obstacleDetected, sensorData])

  // Gradually increase speed when conditions are safe
  useEffect(() => {
    if (!connected || currentMode !== '1') {
      if (speedIncreaseIntervalRef.current) {
        clearInterval(speedIncreaseIntervalRef.current)
        speedIncreaseIntervalRef.current = null
      }
      return
    }

    // Only increase speed if:
    // - Not stuck
    // - No obstacles detected
    // - Current speed is less than base speed
    if (!isStuck && !obstacleDetected && effectiveSpeed < baseSpeed) {
      const interval = setInterval(() => {
        setEffectiveSpeed(prev => {
          const newSpeed = Math.min(baseSpeed, prev + 5) // Increase by 5% every 2 seconds
          if (newSpeed !== prev) {
            console.log(`📈 Gradually increasing speed: ${prev}% → ${newSpeed}%`)
          }
          return newSpeed
        })
      }, 2000) // Check every 2 seconds

      speedIncreaseIntervalRef.current = interval

      return () => {
        if (interval) clearInterval(interval)
      }
    } else {
      if (speedIncreaseIntervalRef.current) {
        clearInterval(speedIncreaseIntervalRef.current)
        speedIncreaseIntervalRef.current = null
      }
    }
  }, [connected, currentMode, isStuck, obstacleDetected, effectiveSpeed, baseSpeed])

  // Reset effective speed when mode changes or disconnects
  useEffect(() => {
    if (!connected) {
      setEffectiveSpeed(50)
      setIsStuck(false)
      setObstacleDetected(false)
      frameChangeCountRef.current = 0
      previousFrameRef.current = null
    } else if (currentMode !== '1') {
      // Not in Move mode - use base speed
      setEffectiveSpeed(baseSpeed)
      setIsStuck(false)
      setObstacleDetected(false)
    } else if (currentMode === '1') {
      // Entering Move mode - start at 50%
      const initialSpeed = Math.max(50, Math.round(baseSpeed * 0.5))
      setEffectiveSpeed(initialSpeed)
      setIsStuck(false)
      setObstacleDetected(false)
      frameChangeCountRef.current = 0
      previousFrameRef.current = null
      console.log(`🚀 Entering Move mode: Starting at ${initialSpeed}% (50% of ${baseSpeed}%)`)
    }
  }, [connected, currentMode, baseSpeed])

  // Cleanup intervals
  useEffect(() => {
    return () => {
      if (stuckCheckIntervalRef.current) {
        clearInterval(stuckCheckIntervalRef.current)
      }
      if (speedIncreaseIntervalRef.current) {
        clearInterval(speedIncreaseIntervalRef.current)
      }
    }
  }, [])

  return {
    effectiveSpeed,
    isStuck,
    obstacleDetected
  }
}

