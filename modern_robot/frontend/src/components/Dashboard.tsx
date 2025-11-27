import React, { useState } from 'react';
import { Joystick } from 'react-joystick-component';
import { Camera, Zap, Shield, Trash2, UserCheck, RotateCcw } from 'lucide-react';
import { Socket } from 'socket.io-client';

interface DashboardProps {
  socket: Socket;
  robotState: any;
  robotIp: string;
}

const Dashboard: React.FC<DashboardProps> = ({ socket, robotState, robotIp }) => {
  const [rearCamAngle, setRearCamAngle] = useState(90);
  const [armLift, setArmLift] = useState(90);
  const [clawOpen, setClawOpen] = useState(90);

  const handleMove = (event: any) => {
    socket.emit('control_command', {
        command: 'move',
        params: { x: event.x, y: event.y }
    });
  };

  const handleStop = () => {
    socket.emit('control_command', {
        command: 'move',
        params: { x: 0, y: 0 }
    });
  };
  
  const setAutonomy = (level: string) => {
      socket.emit('set_autonomy', { level });
  };

  const updateServo = (joint: string, value: number) => {
      if (joint === 'rear_cam') {
          setRearCamAngle(value);
          socket.emit('control_command', {
              command: 'camera_pan',
              params: { angle: value }
          });
      } else {
          if (joint === 'lift') setArmLift(value);
          if (joint === 'claw') setClawOpen(value);
          
          socket.emit('control_command', {
              command: 'arm_control',
              params: { joint, value }
          });
      }
  };

  const getVideoUrl = (cam: string) => {
      return `http://${robotIp}:8000/api/video/${cam}`;
  };

  return (
    <div className="grid grid-cols-12 gap-4 h-full p-4">
      {/* Left Panel: Camera & Status */}
      <div className="col-span-8 flex flex-col gap-4">
        {/* Video Feeds Grid */}
        <div className="flex-1 grid grid-cols-2 gap-4 h-[50vh]">
            <div className="bg-black rounded-2xl relative overflow-hidden border border-gray-800 flex items-center justify-center group">
                <img 
                    src={getVideoUrl('front')} 
                    className="absolute inset-0 w-full h-full object-cover"
                    alt="Front Camera"
                    onError={(e) => {e.currentTarget.style.display = 'none'}} 
                />
                <div className="absolute top-4 left-4 bg-black/50 backdrop-blur px-3 py-1 rounded-full text-xs font-mono text-green-400 z-10">
                    FRONT CAMERA
                </div>
            </div>
            
            <div className="bg-black rounded-2xl relative overflow-hidden border border-gray-800 flex items-center justify-center group">
                <img 
                    src={getVideoUrl('rear')} 
                    className="absolute inset-0 w-full h-full object-cover"
                    alt="Rear Camera"
                    onError={(e) => {e.currentTarget.style.display = 'none'}}
                />
                <div className="absolute top-4 left-4 bg-black/50 backdrop-blur px-3 py-1 rounded-full text-xs font-mono text-yellow-400 z-10">
                    REAR CAMERA
                </div>
                
                {/* Rear Cam Controls Overlay */}
                <div className="absolute bottom-4 left-4 right-4 bg-black/60 backdrop-blur rounded-lg p-2 flex items-center gap-2 z-20 opacity-0 group-hover:opacity-100 transition-opacity">
                    <RotateCcw size={16} className="text-gray-400" />
                    <input 
                        type="range" 
                        min="0" max="180" 
                        value={rearCamAngle}
                        onChange={(e) => updateServo('rear_cam', parseInt(e.target.value))}
                        className="flex-1 h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-yellow-400"
                    />
                </div>
            </div>
        </div>
        
        {/* Sensor Data */}
        <div className="h-48 bg-robot-panel rounded-2xl p-4 grid grid-cols-4 gap-4">
            <div className="bg-gray-800/50 rounded-xl p-3">
                <div className="text-gray-400 text-sm mb-1">Battery</div>
                <div className="text-2xl font-bold text-green-400">{robotState?.battery?.toFixed(1) || 100}%</div>
            </div>
            <div className="bg-gray-800/50 rounded-xl p-3">
                <div className="text-gray-400 text-sm mb-1">Ultrasonic</div>
                <div className="text-2xl font-bold text-blue-400">{robotState?.sensors?.ultrasonic?.toFixed(1) || '--'} cm</div>
            </div>
             <div className="bg-gray-800/50 rounded-xl p-3">
                <div className="text-gray-400 text-sm mb-1">Status</div>
                <div className="text-xl font-bold text-white capitalize">{robotState?.status || 'Offline'}</div>
            </div>
             <div className="bg-gray-800/50 rounded-xl p-3">
                <div className="text-gray-400 text-sm mb-1">Robot IP</div>
                <div className="text-sm font-mono text-gray-300 break-all">{robotIp}</div>
            </div>
        </div>
      </div>

      {/* Right Panel: Controls */}
      <div className="col-span-4 bg-robot-panel rounded-2xl p-6 flex flex-col gap-6 border-l border-gray-800 overflow-y-auto">
        
        {/* Autonomy Selector */}
        <div>
            <h3 className="text-gray-400 text-xs font-bold tracking-wider mb-3">AUTONOMY LEVEL</h3>
            <div className="flex bg-gray-900 rounded-lg p-1">
                {['manual', 'semi', 'auto'].map((mode) => (
                    <button
                        key={mode}
                        onClick={() => setAutonomy(mode)}
                        className={`flex-1 py-2 rounded-md text-sm font-medium transition-all ${
                            robotState?.autonomy_level === mode 
                            ? 'bg-robot-accent text-black shadow-lg shadow-robot-accent/20' 
                            : 'text-gray-400 hover:text-white'
                        }`}
                    >
                        {mode.toUpperCase()}
                    </button>
                ))}
            </div>
        </div>

        {/* Manual Controls */}
        <div className="flex flex-col items-center justify-center bg-gray-900/50 rounded-xl border border-dashed border-gray-800 p-4">
             <div className="mb-4 text-xs text-gray-500 font-mono">MOVEMENT CONTROL</div>
             <Joystick 
                size={120} 
                sticky={false} 
                baseColor="#2a2a2a" 
                stickColor="#00ff88" 
                move={handleMove} 
                stop={handleStop}
            />
        </div>
        
        {/* Arm Controls */}
        <div className="bg-gray-900/50 rounded-xl p-4 border border-dashed border-gray-800">
             <div className="mb-4 text-xs text-gray-500 font-mono">ROBOT ARM</div>
             
             <div className="space-y-4">
                 <div>
                     <div className="flex justify-between text-xs text-gray-400 mb-1">
                         <span>LIFT HEIGHT</span>
                         <span>{armLift}°</span>
                     </div>
                     <input 
                        type="range" 
                        min="0" max="180" 
                        value={armLift}
                        onChange={(e) => updateServo('lift', parseInt(e.target.value))}
                        className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-400"
                    />
                 </div>
                 
                 <div>
                     <div className="flex justify-between text-xs text-gray-400 mb-1">
                         <span>CLAW GRIP</span>
                         <span>{clawOpen}°</span>
                     </div>
                     <input 
                        type="range" 
                        min="0" max="180" 
                        value={clawOpen}
                        onChange={(e) => updateServo('claw', parseInt(e.target.value))}
                        className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-purple-400"
                    />
                 </div>
             </div>
        </div>
        
        {/* AI Actions */}
        <div>
             <h3 className="text-gray-400 text-xs font-bold tracking-wider mb-3">QUICK ACTIONS</h3>
             <div className="grid grid-cols-2 gap-2">
                 <button className="bg-gray-700 hover:bg-gray-600 p-3 rounded-lg flex items-center justify-center gap-2 transition-colors">
                     <UserCheck size={18} />
                     <span className="text-sm">Scan Face</span>
                 </button>
                 <button className="bg-gray-700 hover:bg-gray-600 p-3 rounded-lg flex items-center justify-center gap-2 transition-colors">
                     <Trash2 size={18} />
                     <span className="text-sm">Pickup</span>
                 </button>
             </div>
        </div>

      </div>
    </div>
  );
};

export default Dashboard;
