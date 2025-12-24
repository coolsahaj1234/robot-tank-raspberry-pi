import React, { useState, useEffect, useCallback } from 'react'
import EnhancedVideoView from './EnhancedVideoView'
import ControlPanel from './ControlPanel'
import AIChatPanel from './AIChatPanel'
import SettingsPanel from './SettingsPanel'
import ModeSelector from './ModeSelector'
import { useAIVideoProcessor } from '../hooks/useAIVideoProcessor'
import { useAutonomousNavigation } from '../hooks/useAutonomousNavigation'
import { Play, Square, Settings, Wifi, WifiOff, Activity } from 'lucide-react'
import './Dashboard.css'

export default function Dashboard({
  connected,
  connecting,
  onConnect,
  onDisconnect,
  onSendCommand,
  videoFrame,
  sensorData
}) {
  const [showSettings, setShowSettings] = useState(false)
  const [currentMode, setCurrentMode] = useState('0')
  const [autonomousEnabled, setAutonomousEnabled] = useState(false)
  const [settings, setSettings] = useState({
    ip: localStorage.getItem('robotIP') || '10.0.0.86',
    commandPort: localStorage.getItem('commandPort') || '5003',
    videoPort: localStorage.getItem('videoPort') || '8003'
  })

  const handleConnect = () => {
    onConnect(
      settings.ip,
      parseInt(settings.commandPort),
      parseInt(settings.videoPort)
    )
  }

  // Reset autonomous mode when disconnecting or leaving AI mode
  useEffect(() => {
    if (!connected || currentMode !== '4') {
      setAutonomousEnabled(false)
    }
  }, [connected, currentMode])

  // AI processing enabled for ALL modes when connected (not just AI mode)
  const {
    processedFrame,
    laneData,
    obstacleData,
    navigationCommand,
    radarData,
    navigationState,
    thinkingLog,
    narration,
    detectedObjects,
    processing: aiProcessing,
    error: aiError
  } = useAIVideoProcessor(videoFrame, connected, sensorData)

  // Autonomous navigation only in AI mode when user enables it
  const isAIMode = currentMode === '4'
  useAutonomousNavigation({
    enabled: isAIMode && connected && autonomousEnabled,
    navigationCommand,
    onSendCommand
  })

  // Click-to-navigate handler for manual control
  const handleClickNavigate = useCallback((direction, speed) => {
    if (!connected || !onSendCommand) return

    onSendCommand({ type: 'move', direction, speed })

    // Auto-stop after brief movement
    setTimeout(() => {
      onSendCommand({ type: 'move', direction: 'stop', speed: 0 })
    }, 800)
  }, [connected, onSendCommand])

  // Danger zone for display
  const dangerZone = obstacleData?.danger_zone || navigationCommand?.danger_zone || 'clear'

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-left">
          <div className="logo">
            <div className="logo-icon">🤖</div>
            <div>
              <h1>Robot Tank Controller</h1>
              <p className="subtitle">AI-Enhanced Dashboard</p>
            </div>
          </div>
        </div>

        <div className="header-right">
          <div className={`status-indicator ${connected ? 'connected' : 'disconnected'}`}>
            {connected ? <Wifi size={16} /> : <WifiOff size={16} />}
            <span>{connected ? 'Connected' : 'Disconnected'}</span>
          </div>

          <button
            className={`connect-btn ${connected ? 'connected' : ''}`}
            onClick={connected ? onDisconnect : handleConnect}
            disabled={connecting}
          >
            {connecting ? (
              <>
                <Activity size={16} className="spinning" /> Connecting...
              </>
            ) : connected ? (
              <>
                <Square size={16} /> Disconnect
              </>
            ) : (
              <>
                <Play size={16} /> Connect
              </>
            )}
          </button>

          <button
            className="settings-btn"
            onClick={() => setShowSettings(!showSettings)}
            title="Settings"
          >
            <Settings size={20} />
          </button>
        </div>
      </header>

      <div className="dashboard-content">
        {/* Main video area with AI enhancements - same for all modes */}
        <div className="main-panel">
          <EnhancedVideoView
            videoFrame={videoFrame}
            processedFrame={processedFrame}
            connected={connected}
            sensorData={sensorData}
            obstacleData={obstacleData}
            radarData={radarData}
            detectedObjects={detectedObjects}
            navigationCommand={navigationCommand}
            aiError={aiError}
            autonomousActive={isAIMode && autonomousEnabled}
            onClickNavigate={!isAIMode ? handleClickNavigate : null}
            showClickHints={!isAIMode}
          />
        </div>

        {/* Side panel - different content based on mode */}
        <div className="side-panel">
          {isAIMode ? (
            <AIChatPanel
              connected={connected}
              sensorData={sensorData}
              radarData={radarData}
              detectedObjects={detectedObjects}
              navigationCommand={navigationCommand}
              narration={narration}
              autonomousEnabled={autonomousEnabled}
              onSetAutonomousEnabled={setAutonomousEnabled}
              onSendCommand={onSendCommand}
              dangerZone={dangerZone}
            />
          ) : (
            <ControlPanel
              connected={connected}
              onSendCommand={onSendCommand}
              videoFrame={videoFrame}
              sensorData={sensorData}
              currentMode={currentMode}
            />
          )}
        </div>
      </div>

      <div className="bottom-panel">
        <ModeSelector
          connected={connected}
          onSendCommand={onSendCommand}
          onModeChange={setCurrentMode}
        />
      </div>

      {showSettings && (
        <SettingsPanel
          settings={settings}
          onChange={setSettings}
          onClose={() => setShowSettings(false)}
        />
      )}
    </div>
  )
}
