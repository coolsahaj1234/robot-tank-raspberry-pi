import React, { useState, useEffect, useRef } from 'react'
import { Radar, Wifi, WifiOff, Video, VideoOff } from 'lucide-react'
import './VideoView.css'

export default function VideoView({ frame, connected, sensorData, settings, showOverlays = true }) {
  const [frameCount, setFrameCount] = useState(0)
  const [fps, setFps] = useState(0)
  const lastFrameTimeRef = useRef(Date.now())
  const fpsHistoryRef = useRef([])
  const frameCountRef = useRef(0)
  
  useEffect(() => {
    if (frame) {
      const now = Date.now()
      const timeDiff = now - lastFrameTimeRef.current
      lastFrameTimeRef.current = now
      
      if (timeDiff > 0) {
        const currentFps = 1000 / timeDiff
        fpsHistoryRef.current.push(currentFps)
        if (fpsHistoryRef.current.length > 10) {
          fpsHistoryRef.current.shift()
        }
        const avgFps = fpsHistoryRef.current.reduce((a, b) => a + b, 0) / fpsHistoryRef.current.length
        setFps(Math.round(avgFps))
      }
      
      // Update frame count using functional update
      setFrameCount(prev => {
        const newCount = prev + 1
        frameCountRef.current = newCount
        // Log every 30th frame
        if (newCount % 30 === 0) {
          console.log(`📹 Video frame updated: #${newCount}`)
        }
        return newCount
      })
    }
  }, [frame]) // Only depend on frame, not frameCount
  
  return (
    <div className="video-view">
      <div className="video-container">
        {frame ? (
          <img 
            src={frame} 
            alt="Robot Camera Feed" 
            className="video-frame"
            key={`frame-${frameCount}`}
            onError={(e) => {
              console.error('❌ Error loading video frame:', e)
            }}
            onLoad={() => {
              if (frameCount % 30 === 0) {
                console.log('✅ Video frame loaded successfully')
              }
            }}
          />
        ) : (
          <div className="video-placeholder">
            <div className="placeholder-icon">
              {connected ? <VideoOff size={64} /> : <Video size={64} />}
            </div>
            <div className="placeholder-text">
              {connected ? 'Waiting for video feed...' : 'Not connected'}
            </div>
            {connected && (
              <div className="placeholder-hint">
                Check server console for video connection status
              </div>
            )}
          </div>
        )}
        
        {showOverlays && (
          <>
            {/* Top Left Overlay - Camera Info */}
            <div className="video-overlay video-overlay-top-left">
              <div className="overlay-item">
                <Video size={14} />
                <span>FRONT CAMERA</span>
              </div>
              {frame && (
                <div className="overlay-item">
                  <span className="overlay-label">FPS:</span>
                  <span className="overlay-value">{fps}</span>
                </div>
              )}
            </div>
            
            {/* Top Right Overlay - Connection Status */}
            <div className="video-overlay video-overlay-top-right">
              <div className={`overlay-item ${connected ? 'status-connected' : 'status-disconnected'}`}>
                {connected ? <Wifi size={14} /> : <WifiOff size={14} />}
                <span>{connected ? 'ONLINE' : 'OFFLINE'}</span>
              </div>
              {connected && (
                <div className="overlay-item">
                  <span className="overlay-label">IP:</span>
                  <span className="overlay-value">{settings.ip}</span>
                </div>
              )}
            </div>
            
            {/* Bottom Left Overlay - Sensor Data */}
            {connected && (
              <div className="video-overlay video-overlay-bottom-left">
                {sensorData.distance !== null && (
                  <div className="overlay-item sensor-item">
                    <Radar size={16} className="sensor-icon" />
                    <div className="sensor-info">
                      <span className="sensor-label">Distance</span>
                      <span className="sensor-value">{sensorData.distance.toFixed(1)} cm</span>
                    </div>
                  </div>
                )}
                {sensorData.distanceBack !== null && (
                  <div className="overlay-item sensor-item">
                    <Radar size={16} className="sensor-icon" />
                    <div className="sensor-info">
                      <span className="sensor-label">Rear</span>
                      <span className="sensor-value">{sensorData.distanceBack.toFixed(1)} cm</span>
                    </div>
                  </div>
                )}
              </div>
            )}
            
            {/* Bottom Right Overlay - Frame Counter */}
            {frame && (
              <div className="video-overlay video-overlay-bottom-right">
                <div className="overlay-item">
                  <span className="overlay-label">Frame:</span>
                  <span className="overlay-value">#{frameCount}</span>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

