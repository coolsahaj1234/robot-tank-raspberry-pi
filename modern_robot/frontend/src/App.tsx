import React, { useEffect, useState } from 'react';
import { socket, getRobotIp } from './lib/socket';
import { Wifi, WifiOff, Gamepad2, Settings as SettingsIcon } from 'lucide-react';
import Dashboard from './components/Dashboard';
import SettingsModal from './components/SettingsModal';

function App() {
  const [isConnected, setIsConnected] = useState(socket.connected);
  const [robotState, setRobotState] = useState<any>(null);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [robotIp, setRobotIp] = useState(getRobotIp());

  useEffect(() => {
    function onConnect() {
      setIsConnected(true);
    }

    function onDisconnect() {
      setIsConnected(false);
    }

    function onStatus(value: any) {
       setRobotState(value.robot_state);
    }
    
    function onRobotResponse(value: any) {
        console.log("Robot Response:", value);
    }

    socket.on('connect', onConnect);
    socket.on('disconnect', onDisconnect);
    socket.on('status', onStatus);
    socket.on('robot_response', onRobotResponse);

    return () => {
      socket.off('connect', onConnect);
      socket.off('disconnect', onDisconnect);
      socket.off('status', onStatus);
      socket.off('robot_response', onRobotResponse);
    };
  }, []);

  return (
    <div className="flex h-screen bg-robot-dark text-white font-sans">
      <SettingsModal 
        isOpen={isSettingsOpen} 
        onClose={() => setIsSettingsOpen(false)} 
        onUpdate={(ip) => setRobotIp(ip)}
      />

      {/* Sidebar / Navigation */}
      <nav className="w-16 bg-robot-panel flex flex-col items-center py-4 space-y-6 border-r border-gray-800">
        <div className={`p-2 rounded-full ${isConnected ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
          {isConnected ? <Wifi size={24} /> : <WifiOff size={24} />}
        </div>
        
        <button className="p-3 hover:bg-gray-700 rounded-xl transition-colors text-robot-accent">
          <Gamepad2 size={24} />
        </button>
        
        <div className="flex-1" />
        
        <button 
          onClick={() => setIsSettingsOpen(true)}
          className="p-3 hover:bg-gray-700 rounded-xl transition-colors text-gray-400"
        >
          <SettingsIcon size={24} />
        </button>
      </nav>

      {/* Main Content */}
      <main className="flex-1 overflow-hidden relative">
         <Dashboard socket={socket} robotState={robotState} robotIp={robotIp} />
      </main>
    </div>
  );
}

export default App;
