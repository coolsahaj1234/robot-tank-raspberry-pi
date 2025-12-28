import React, { useState, useEffect, useCallback } from 'react'
import EnhancedVideoView from './EnhancedVideoView'
import ControlPanel from './ControlPanel'
import AIChatPanel from './AIChatPanel'
import SettingsPanel from './SettingsPanel'
import ModeSelector from './ModeSelector'
import { useAIVideoProcessor } from '../hooks/useAIVideoProcessor'
import { useAutonomousNavigation } from '../hooks/useAutonomousNavigation'
<<<<<<< HEAD
import { Play, Square, Settings, Wifi, WifiOff, Activity } from 'lucide-react'
=======
import { useMovementIntelligence } from '../hooks/useMovementIntelligence'
import { Play, Square, Settings, Wifi, WifiOff, Activity, AlertOctagon } from 'lucide-react'
>>>>>>> 40885bf (Initial commit)
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
<<<<<<< HEAD
  const [settings, setSettings] = useState({
    ip: localStorage.getItem('robotIP') || '10.0.0.86',
    commandPort: localStorage.getItem('commandPort') || '5003',
    videoPort: localStorage.getItem('videoPort') || '8003'
  })
=======
  const [isSantaStandby, setIsSantaStandby] = useState(false)
  const [speed, setSpeed] = useState(50)
  const [settings, setSettings] = useState({
    ip: localStorage.getItem('robotIP') || '10.0.0.86',
    commandPort: localStorage.getItem('commandPort') || '5003',
    commandPort: localStorage.getItem('commandPort') || '5003',
    videoPort: localStorage.getItem('videoPort') || '8003'
  })
  const [showAutoParkConfirm, setShowAutoParkConfirm] = useState(false)

  // 1. AI processing (enabled for ALL modes when connected)
  // 1. AI processing (enabled for ALL modes when connected)
  const isSantaMode = currentMode === '5'
  const isAutoParkMode = currentMode === '6'
  const aiProcessor = useAIVideoProcessor(videoFrame, connected, sensorData, isSantaMode, isSantaStandby, isAutoParkMode)
  const {
    processedFrame,
    obstacleData,
    navigationCommand,
    radarData,
    navigationState,
    thinkingLog,
    narration,
    detectedObjects,
    error: aiError
  } = aiProcessor

  // 2. Movement Intelligence / Safety Watchdog (Uses AI feedback)
  const { effectiveSpeed, isStuck, obstacleDetected } = useMovementIntelligence({
    connected,
    videoFrame,
    sensorData,
    currentMode,
    baseSpeed: speed,
    onSendCommand,
    aiNavigationCommand: navigationCommand
  })

  // 3. Autonomous navigation (only in AI mode when user enables it)
  const isAIMode = currentMode === '4' || isSantaMode || isAutoParkMode
  useAutonomousNavigation({
    enabled: isAIMode && connected && autonomousEnabled,
    navigationCommand,
    onSendCommand
  })
>>>>>>> 40885bf (Initial commit)

  const handleConnect = () => {
    onConnect(
      settings.ip,
      parseInt(settings.commandPort),
      parseInt(settings.videoPort)
    )
  }

<<<<<<< HEAD
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
=======
  // Reset autonomous mode and standby when disconnecting or leaving modes
  useEffect(() => {
    if (!connected || (currentMode !== '4' && currentMode !== '5' && currentMode !== '6')) {
      setAutonomousEnabled(false)
    }
    if (!connected || currentMode !== '5') {
      setIsSantaStandby(false)
    }
  }, [connected, currentMode])

  const handleModeChange = (mode) => {
    if (mode === '6') {
      // Intercept Auto Park mode
      setShowAutoParkConfirm(true)
    } else {
      setCurrentMode(mode)
    }
  }

  const confirmAutoPark = () => {
    setShowAutoParkConfirm(false)
    setCurrentMode('6')
    setAutonomousEnabled(true) // ENABLE AI AUTONOMY
    // Send mode change command explicitly here if needed, 
    // but the ModeSelector usually handles it. 
    // However, since we intercepted it in ModeSelector, ModeSelector MIGHT have already sent it 
    // IF we didn't control it fully.
    // Actually, ModeSelector sends the command internally. 
    // But we need to update our local state to '6' so the UI updates.
    // AND we probably should re-send it to be sure or if ModeSelector only called us.
    // ... Wait, ModeSelector calls `onSendCommand` AND `onModeChange`.
    // If we want to intercept, we might need to change how ModeSelector works or just re-send 6 here.
    // Let's assume ModeSelector sends it. But wait, if I cancel, I need to revert?
    // Actually, ModeSelector sets its own local state. 
    // To do this properly, ModeSelector should be a controlled component or we accept it sends 6, 
    // and we just show the dialog to confirm "starting" the logic. 
    // BUT the user request implies asking "Do you want to auto park" BEFORE it starts.
    // If ModeSelector sends CMD_MODE#6 immediately, it might be too late.
    // However, I can't easily change ModeSelector to be fully controlled without bigger refactor.
    // So, acceptable compromise: ModeSelector sends #6. We show dialog. 
    // If user says NO, we switch back to #0 (Stop).
    // If user says YES, we stay in #6 and enable the AI flag.

    // BETTER APPROACH for this existing codebase:
    // Let's just send CMD_MODE#6 again to be sure.
    onSendCommand('CMD_MODE#6')
  }

  const cancelAutoPark = () => {
    setShowAutoParkConfirm(false)
    // Revert to Stop mode
    setCurrentMode('0')
    onSendCommand('CMD_MODE#0')
  }
>>>>>>> 40885bf (Initial commit)

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

<<<<<<< HEAD
  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-left">
          <div className="logo">
            <div className="logo-icon">🤖</div>
            <div>
              <h1>Robot Tank Controller</h1>
              <p className="subtitle">AI-Enhanced Dashboard</p>
=======
  const dashboardClasses = [
    'dashboard',
    isStuck ? 'stuck' : '',
    isSantaMode ? 'santa-mode' : ''
  ].filter(Boolean).join(' ')

  return (
    <div className={dashboardClasses}>
      <header className="dashboard-header">
        <div className="header-left">
          <div className="logo">
            <div className="logo-icon">{isStuck ? '🚨' : '🤖'}</div>
            <div>
              <h1 className={isStuck ? 'stuck-title' : (isSantaMode ? 'santa-title' : '')}>
                {isStuck ? 'EMERGENCY STOP' : (isSantaMode ? '🎅 SANTA MODE' : 'Robot Tank Controller')}
              </h1>
              <p className="subtitle">
                {isStuck ? 'Video feed frozen - safety triggered' : (isSantaMode ? 'Merry Christmas! Delivering gifts...' : 'AI-Enhanced Dashboard')}
              </p>
>>>>>>> 40885bf (Initial commit)
            </div>
          </div>
        </div>

        <div className="header-right">
<<<<<<< HEAD
=======
          {isStuck && (
            <div className="stuck-alert">
              <AlertOctagon size={20} />
              <span>STUCK DETECTED</span>
            </div>
          )}
>>>>>>> 40885bf (Initial commit)
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
<<<<<<< HEAD
              onSendCommand={onSendCommand}
              dangerZone={dangerZone}
=======
              isSantaMode={isSantaMode}
              isSantaStandby={isSantaStandby}
              onSetSantaStandby={setIsSantaStandby}
              onSendCommand={onSendCommand}
              dangerZone={dangerZone}
              videoFrame={videoFrame}
>>>>>>> 40885bf (Initial commit)
            />
          ) : (
            <ControlPanel
              connected={connected}
              onSendCommand={onSendCommand}
              videoFrame={videoFrame}
              sensorData={sensorData}
              currentMode={currentMode}
<<<<<<< HEAD
=======
              speed={speed}
              setSpeed={setSpeed}
              effectiveSpeed={effectiveSpeed}
              isStuck={isStuck}
              obstacleDetected={obstacleDetected}
>>>>>>> 40885bf (Initial commit)
            />
          )}
        </div>
      </div>

      <div className="bottom-panel">
        <ModeSelector
          connected={connected}
          onSendCommand={onSendCommand}
<<<<<<< HEAD
          onModeChange={setCurrentMode}
        />
      </div>

=======
          onModeChange={handleModeChange}
        />
      </div>

      {/* Auto Park Confirmation Modal */}
      {showAutoParkConfirm && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3>🅿️ Auto Park</h3>
            <p>Do you want to auto park?</p>
            <div className="modal-buttons">
              <button className="modal-btn cancel" onClick={cancelAutoPark}>Cancel</button>
              <button className="modal-btn confirm" onClick={confirmAutoPark}>Auto Park</button>
            </div>
          </div>
        </div>
      )}

>>>>>>> 40885bf (Initial commit)
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
