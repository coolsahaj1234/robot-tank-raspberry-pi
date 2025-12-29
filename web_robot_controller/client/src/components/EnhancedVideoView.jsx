import React, { useState, useEffect, useRef, useCallback } from 'react'
import RadarView from './RadarView'
import { Eye, AlertCircle, Target, ArrowUp, ArrowDown, ArrowLeft, ArrowRight, Compass, Activity, Brain } from 'lucide-react'
import './EnhancedVideoView.css'

/**
 * EnhancedVideoView - Unified video view with AI overlays
 * Used for both manual and AI modes
 * Shows: processed video, object detection, radar, distance indicators
 * AI action overlays only shown when autonomousActive=true
 */
export default function EnhancedVideoView({
  videoFrame,
  processedFrame,
  connected,
  sensorData,
  obstacleData,
  radarData,
  detectedObjects = [],
  navigationCommand,
  aiError,
  autonomousActive = false,  // Only show AI decisions when this is true
  onClickNavigate,
  showClickHints = false
}) {
  const videoContainerRef = useRef(null)
  const [clickTarget, setClickTarget] = useState(null)

  // Use raw sensor data for accurate readings
  const frontDistance = sensorData?.distance ?? radarData?.ultrasonic_distance ?? 0
  const backDistance = sensorData?.distanceBack ?? radarData?.ultrasonic_distance_back ?? 0

  // Handle click-to-navigate
  const handleVideoClick = useCallback((e) => {
    if (!connected || !onClickNavigate) return

    const rect = e.currentTarget.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top
    const width = rect.width
    const height = rect.height

    const relX = x / width
    const relY = y / height

    setClickTarget({ x, y, relX, relY, timestamp: Date.now() })

    // Determine direction based on click position
    let direction, speed
    if (relX < 0.33) {
      direction = 'left'
      speed = 60
    } else if (relX > 0.67) {
      direction = 'right'
      speed = 60
    } else if (relY < 0.4) {
      direction = 'forward'
      speed = 50
    } else if (relY > 0.7) {
      direction = 'backward'
      speed = 50
    } else {
      direction = 'forward'
      speed = 40
    }

    onClickNavigate(direction, speed)
  }, [connected, onClickNavigate])

  // Clear click target after animation
  useEffect(() => {
    if (clickTarget) {
      const timer = setTimeout(() => setClickTarget(null), 1200)
      return () => clearTimeout(timer)
    }
  }, [clickTarget])

  // Get distance color class
  const getDistanceClass = (distance, isBack = false) => {
    const danger = isBack ? 15 : 25
    const caution = isBack ? 30 : 50
    if (distance < danger) return 'danger'
    if (distance < caution) return 'caution'
    return 'clear'
  }

  return (
    <div className="enhanced-video-view">
      <div className="video-main-area">
        {/* Main video display */}
        <div
          className={`video-container ${onClickNavigate ? 'clickable' : ''}`}
          ref={videoContainerRef}
          onClick={onClickNavigate ? handleVideoClick : undefined}
        >
          {/* Camera label - Top Left */}
          <div className="video-label">
            <Eye size={14} />
            <span>{autonomousActive ? 'AI Autonomous' : 'AI Enhanced'}</span>
            {autonomousActive && (
              <span className="nav-state active">AUTO</span>
            )}
          </div>

          {/* Detected Objects - Top Right */}
          {detectedObjects.length > 0 && (
            <div className="objects-indicator">
              <Target size={14} />
              <span>{detectedObjects.length} Objects</span>
              <div className="objects-popup">
                {detectedObjects.map((obj, i) => (
                  <div key={i} className="object-item">
                    {obj.type} ({(obj.confidence * 100).toFixed(0)}%)
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Zone indicators - Top Center, moved down slightly to avoid label */}
          {autonomousActive && obstacleData && (
            <div className="zone-overlay">
              <div className={`zone-indicator left ${obstacleData.left_clear !== false ? 'clear' : 'blocked'}`}>
                L {obstacleData.left_clear !== false ? '✓' : '✗'}
              </div>
              <div className={`zone-indicator center ${obstacleData.center_blocked !== true ? 'clear' : 'blocked'}`}>
                C {obstacleData.center_blocked !== true ? '✓' : '✗'}
              </div>
              <div className={`zone-indicator right ${obstacleData.right_clear !== false ? 'clear' : 'blocked'}`}>
                R {obstacleData.right_clear !== false ? '✓' : '✗'}
              </div>
            </div>
          )}

          {/* Main video area content remains same */}
          {aiError ? (
            <div className="video-error">
              <AlertCircle size={24} />
              <span>AI Service: {aiError}</span>
            </div>
          ) : (autonomousActive && processedFrame) ? (
            <img src={processedFrame} alt="AI Autonomous Feed" className="video-frame" />
          ) : videoFrame ? (
            <img src={videoFrame} alt="Camera Feed" className="video-frame" />
          ) : (
            <div className="video-placeholder">
              <Eye size={48} className="placeholder-icon" />
              <span>{connected ? 'Waiting for video...' : 'Connect to robot'}</span>
            </div>
          )}

          {/* IMU & Gyro Telemetry - Bottom Left */}
          {sensorData?.imu && (
            <div className="imu-overlay">
              <div className="imu-section">
                <Compass size={14} />
                <span>GYRO</span>
                <div className="imu-grid">
                  <div className="imu-val">X: {sensorData.imu.gyro.x.toFixed(1)}°</div>
                  <div className="imu-val">Y: {sensorData.imu.gyro.y.toFixed(1)}°</div>
                </div>
              </div>
              <div className="imu-section">
                <Activity size={14} />
                <span>ACCEL</span>
                <div className="imu-grid">
                  <div className="imu-val">X: {sensorData.imu.accel.x.toFixed(2)}G</div>
                  <div className="imu-val">Y: {sensorData.imu.accel.y.toFixed(2)}G</div>
                </div>
              </div>
            </div>
          )}

          {/* Distance indicators - Bottom Right, made more compact */}
          <div className="distance-overlay-compact">
            <div className={`dist-badge front ${getDistanceClass(frontDistance)}`}>
              <ArrowUp size={12} />
              <span>{Math.round(frontDistance)}cm</span>
            </div>
            <div className={`dist-badge back ${getDistanceClass(backDistance, true)}`}>
              <ArrowDown size={12} />
              <span>{Math.round(backDistance)}cm</span>
            </div>
          </div>

          {/* Action indicator - Bottom Center */}
          {autonomousActive && navigationCommand?.action && (
            <div className="ai-action-overlay">
              <div className={`action-badge ${navigationCommand.action}`}>
                <Brain size={16} />
                <span>{navigationCommand.action.toUpperCase().replace('_', ' ')}</span>
              </div>
            </div>
          )}

          {/* Click target indicator */}
          {clickTarget && (
            <div className="click-target" style={{ left: clickTarget.x, top: clickTarget.y }}>
              <Target size={36} className="target-icon" />
              <span className="click-direction">
                {clickTarget.relX < 0.33 ? 'LEFT' :
                  clickTarget.relX > 0.67 ? 'RIGHT' :
                    clickTarget.relY < 0.4 ? 'FORWARD' :
                      clickTarget.relY > 0.7 ? 'BACK' : 'GO'}
              </span>
            </div>
          )}

          {/* Click hints overlay */}
          {showClickHints && onClickNavigate && (
            <div className="click-hints">
              <div className="hint-zone left"><ArrowLeft size={20} /></div>
              <div className="hint-zone center"><ArrowUp size={20} /></div>
              <div className="hint-zone right"><ArrowRight size={20} /></div>
            </div>
          )}
        </div>
      </div>

      {/* Radar sidebar */}
      <div className="radar-sidebar">
        <RadarView
          radarData={radarData}
          sensorData={sensorData}
          dangerZone={frontDistance < 25 ? 'danger' : frontDistance < 50 ? 'caution' : 'clear'}
        />

        {/* Quick stats */}
        <div className="quick-stats">
          <div className={`stat-item ${getDistanceClass(frontDistance)}`}>
            <span className="stat-label">Front</span>
            <span className="stat-value">{Math.round(frontDistance)}cm</span>
          </div>
          <div className={`stat-item ${getDistanceClass(backDistance, true)}`}>
            <span className="stat-label">Back</span>
            <span className="stat-value">{Math.round(backDistance)}cm</span>
          </div>
        </div>
      </div>
    </div>
  )
}
