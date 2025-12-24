import React, { useState, useEffect, useRef } from 'react'
import Dashboard from './components/Dashboard'
import { useRobotConnection } from './hooks/useRobotConnection'
import './App.css'

function App() {
  const {
    connected,
    connecting,
    connect,
    disconnect,
    sendCommand,
    videoFrame,
    sensorData
  } = useRobotConnection()

  return (
    <div className="app">
      <Dashboard
        connected={connected}
        connecting={connecting}
        onConnect={connect}
        onDisconnect={disconnect}
        onSendCommand={sendCommand}
        videoFrame={videoFrame}
        sensorData={sensorData}
      />
    </div>
  )
}

export default App

