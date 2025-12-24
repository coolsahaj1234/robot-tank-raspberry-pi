import React, { useEffect, useRef, useMemo } from 'react'
import './RadarView.css'

/**
 * Radar View Component
 * Displays ultrasonic sensor data, robot position, and movement path
 * Optimized for 2 ultrasonic sensors + front camera setup
 */
export default function RadarView({
  radarData,
  sensorData,
  dangerZone
}) {
  const canvasRef = useRef(null)
  const animationRef = useRef(null)
  const sweepAngleRef = useRef(0)

  // Radar configuration
  const config = useMemo(() => ({
    size: 200,
    center: 100,
    maxRange: 200,  // cm
    rings: 4,
    sweepSpeed: 2,
    colors: {
      background: '#0a1628',
      grid: '#1a3a5c',
      sweep: 'rgba(0, 255, 128, 0.3)',
      robot: '#00ff80',
      obstacle: '#ff4444',
      path: '#00aaff',
      text: '#88ccff',
      danger: '#ff4444',
      caution: '#ffaa00',
      clear: '#00ff80'
    }
  }), [])

  // Draw the radar
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    const { size, center, maxRange, rings, colors } = config

    const draw = () => {
      // Clear canvas
      ctx.fillStyle = colors.background
      ctx.fillRect(0, 0, size, size)

      // Draw grid rings
      ctx.strokeStyle = colors.grid
      ctx.lineWidth = 1
      for (let i = 1; i <= rings; i++) {
        const radius = (center - 10) * (i / rings)
        ctx.beginPath()
        ctx.arc(center, center, radius, 0, Math.PI * 2)
        ctx.stroke()

        // Draw range labels
        const rangeLabel = Math.round((maxRange / rings) * i)
        ctx.fillStyle = colors.text
        ctx.font = '9px monospace'
        ctx.fillText(`${rangeLabel}cm`, center + 3, center - radius + 10)
      }

      // Draw cross lines
      ctx.beginPath()
      ctx.moveTo(center, 10)
      ctx.lineTo(center, size - 10)
      ctx.moveTo(10, center)
      ctx.lineTo(size - 10, center)
      ctx.stroke()

      // Draw direction labels
      ctx.fillStyle = colors.text
      ctx.font = '10px monospace'
      ctx.textAlign = 'center'
      ctx.fillText('F', center, 18)
      ctx.fillText('B', center, size - 8)
      ctx.textAlign = 'left'
      ctx.fillText('L', 12, center + 4)
      ctx.textAlign = 'right'
      ctx.fillText('R', size - 12, center + 4)

      // Draw sweep line (animated)
      sweepAngleRef.current = (sweepAngleRef.current + config.sweepSpeed) % 360
      const sweepRad = (sweepAngleRef.current * Math.PI) / 180

      // Sweep gradient
      const gradient = ctx.createConicalGradient
        ? ctx.createConicalGradient(center, center, sweepRad)
        : null

      if (!gradient) {
        // Fallback sweep without conic gradient
        ctx.save()
        ctx.translate(center, center)
        ctx.rotate(sweepRad)
        ctx.beginPath()
        ctx.moveTo(0, 0)
        ctx.lineTo(0, -(center - 10))
        ctx.strokeStyle = colors.sweep
        ctx.lineWidth = 2
        ctx.stroke()
        ctx.restore()
      }

      // Draw FRONT ultrasonic detection - prioritize raw sensorData
      const ultrasonicDistance = sensorData?.distance ?? radarData?.ultrasonic_distance
      if (ultrasonicDistance && ultrasonicDistance > 0 && ultrasonicDistance < maxRange) {
        const distanceRatio = ultrasonicDistance / maxRange
        const displayRadius = (center - 10) * distanceRatio

        // Draw detection arc (front 60-degree cone)
        const arcStart = -Math.PI / 2 - Math.PI / 6  // -30 degrees from front
        const arcEnd = -Math.PI / 2 + Math.PI / 6    // +30 degrees from front

        // Color based on danger zone
        let detectionColor = colors.clear
        if (dangerZone === 'danger' || ultrasonicDistance < 25) {
          detectionColor = colors.danger
        } else if (dangerZone === 'caution' || ultrasonicDistance < 50) {
          detectionColor = colors.caution
        }

        // Draw filled detection zone
        ctx.beginPath()
        ctx.moveTo(center, center)
        ctx.arc(center, center, displayRadius, arcStart, arcEnd)
        ctx.closePath()
        ctx.fillStyle = detectionColor + '40'  // Semi-transparent
        ctx.fill()

        // Draw detection arc edge
        ctx.beginPath()
        ctx.arc(center, center, displayRadius, arcStart, arcEnd)
        ctx.strokeStyle = detectionColor
        ctx.lineWidth = 2
        ctx.stroke()

        // Draw distance indicator (front)
        ctx.fillStyle = detectionColor
        ctx.font = 'bold 11px monospace'
        ctx.textAlign = 'center'
        ctx.fillText(`F:${Math.round(ultrasonicDistance)}`, center, center - displayRadius - 8)
      }

      // Draw BACK ultrasonic detection - prioritize raw sensorData
      const backDistance = sensorData?.distanceBack ?? radarData?.ultrasonic_distance_back
      if (backDistance && backDistance > 0 && backDistance < maxRange) {
        const distanceRatio = backDistance / maxRange
        const displayRadius = (center - 10) * distanceRatio

        // Draw detection arc (back 60-degree cone)
        const arcStart = Math.PI / 2 - Math.PI / 6  // -30 degrees from back
        const arcEnd = Math.PI / 2 + Math.PI / 6    // +30 degrees from back

        // Color based on distance
        let backColor = colors.clear
        if (backDistance < 20) {
          backColor = colors.danger
        } else if (backDistance < 40) {
          backColor = colors.caution
        }

        // Draw filled detection zone
        ctx.beginPath()
        ctx.moveTo(center, center)
        ctx.arc(center, center, displayRadius, arcStart, arcEnd)
        ctx.closePath()
        ctx.fillStyle = backColor + '40'  // Semi-transparent
        ctx.fill()

        // Draw detection arc edge
        ctx.beginPath()
        ctx.arc(center, center, displayRadius, arcStart, arcEnd)
        ctx.strokeStyle = backColor
        ctx.lineWidth = 2
        ctx.stroke()

        // Draw distance indicator (back)
        ctx.fillStyle = backColor
        ctx.font = 'bold 11px monospace'
        ctx.textAlign = 'center'
        ctx.fillText(`B:${Math.round(backDistance)}`, center, center + displayRadius + 16)
      }

      // Draw path history
      if (radarData?.path_history && radarData.path_history.length > 1) {
        ctx.beginPath()
        ctx.strokeStyle = colors.path
        ctx.lineWidth = 1.5
        ctx.globalAlpha = 0.6

        const pathScale = (center - 10) / 100  // Scale path to radar

        radarData.path_history.forEach((point, index) => {
          const x = center + (point.x * pathScale)
          const y = center - (point.y * pathScale)  // Invert Y for display

          if (index === 0) {
            ctx.moveTo(x, y)
          } else {
            ctx.lineTo(x, y)
          }
        })
        ctx.stroke()
        ctx.globalAlpha = 1.0
      }

      // Draw obstacles from map
      if (radarData?.obstacle_map) {
        const pathScale = (center - 10) / 100
        radarData.obstacle_map.forEach(obs => {
          const x = center + (obs.x * pathScale)
          const y = center - (obs.y * pathScale)

          ctx.beginPath()
          ctx.arc(x, y, 4, 0, Math.PI * 2)
          ctx.fillStyle = colors.obstacle
          ctx.fill()
        })
      }

      // Draw robot position (center with heading)
      const heading = radarData?.heading || 0
      const headingRad = (heading * Math.PI) / 180 - Math.PI / 2  // Adjust for top = 0

      ctx.save()
      ctx.translate(center, center)
      ctx.rotate(headingRad + Math.PI / 2)

      // Robot body (triangle)
      ctx.beginPath()
      ctx.moveTo(0, -8)  // Front
      ctx.lineTo(-6, 6)  // Back left
      ctx.lineTo(6, 6)   // Back right
      ctx.closePath()
      ctx.fillStyle = colors.robot
      ctx.fill()

      // Direction indicator
      ctx.beginPath()
      ctx.moveTo(0, -8)
      ctx.lineTo(0, -14)
      ctx.strokeStyle = colors.robot
      ctx.lineWidth = 2
      ctx.stroke()

      ctx.restore()

      // Request next frame
      animationRef.current = requestAnimationFrame(draw)
    }

    draw()

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
    }
  }, [config, radarData, sensorData, dangerZone])

  return (
    <div className="radar-container">
      <div className="radar-header">
        <span className="radar-title">RADAR</span>
      </div>

      <canvas
        ref={canvasRef}
        width={200}
        height={200}
        className="radar-canvas"
      />

      <div className="radar-stats">
        <div className="stat-row">
          <span className="stat-label">FRONT</span>
          <span
            className="stat-value"
            style={{
              color: dangerZone === 'danger' ? '#ff4444' :
                     dangerZone === 'caution' ? '#ffaa00' : '#00ff80'
            }}
          >
            {Math.round(sensorData?.distance ?? radarData?.ultrasonic_distance ?? 0)}cm
          </span>
        </div>
        <div className="stat-row">
          <span className="stat-label">BACK</span>
          <span
            className="stat-value"
            style={{
              color: (sensorData?.distanceBack ?? radarData?.ultrasonic_distance_back ?? 100) < 20 ? '#ff4444' :
                     (sensorData?.distanceBack ?? radarData?.ultrasonic_distance_back ?? 100) < 40 ? '#ffaa00' : '#00ff80'
            }}
          >
            {Math.round(sensorData?.distanceBack ?? radarData?.ultrasonic_distance_back ?? 0)}cm
          </span>
        </div>
      </div>
    </div>
  )
}
