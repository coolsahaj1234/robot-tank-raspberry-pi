import React, { useState, useEffect } from 'react';
import { Camera, Zap, Shield, Trash2, UserCheck, RotateCcw, Lightbulb, Footprints, AlertOctagon, ZoomIn, ArrowUp, ArrowDown, ArrowLeft, ArrowRight, X } from 'lucide-react';
import { Socket } from 'socket.io-client';

interface DashboardProps {
  socket: Socket;
  robotState: any;
  robotIp: string;
}

const Dashboard: React.FC<DashboardProps> = ({ socket, robotState, robotIp }) => {
  const [rearCamAngle, setRearCamAngle] = useState(90);
  const [armLift, setArmLift] = useState(140);
  const [clawOpen, setClawOpen] = useState(90);
  const [ledColor, setLedColor] = useState("#00ff00");
  const [ledMode, setLedMode] = useState("static");
  const [zoomLevel, setZoomLevel] = useState(1.0);
  const [activeKeys, setActiveKeys] = useState<{ [key: string]: boolean }>({});

  const handleMove = (x: number, y: number) => {
    socket.emit('control_command', {
        command: 'move',
        params: { x, y }
    });
  };

  const handleStop = () => {
    socket.emit('control_command', {
        command: 'move',
        params: { x: 0, y: 0 }
    });
  };

  // Keyboard Control Logic
  useEffect(() => {
    const keysPressed: { [key: string]: boolean } = {};
    
    const updateMovement = () => {
        let x = 0;
        let y = 0;
        if (keysPressed['ArrowUp']) y += 1;
        if (keysPressed['ArrowDown']) y -= 1;
        if (keysPressed['ArrowLeft']) x -= 1;
        if (keysPressed['ArrowRight']) x += 1;
        
        socket.emit('control_command', {
            command: 'move',
            params: { x, y }
        });
        setActiveKeys({...keysPressed});
    };

    const handleKeyDown = (e: KeyboardEvent) => {
        if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
            if (!keysPressed[e.key]) { // Only update if state changes
                keysPressed[e.key] = true;
                updateMovement();
            }
        }
    };

    const handleKeyUp = (e: KeyboardEvent) => {
        if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
            if (keysPressed[e.key]) {
                keysPressed[e.key] = false;
                updateMovement();
            }
        }
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);

    return () => {
        window.removeEventListener('keydown', handleKeyDown);
        window.removeEventListener('keyup', handleKeyUp);
    };
  }, [socket]);
  
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

  const handleZoomChange = (val: number) => {
      setZoomLevel(val);
      socket.emit('control_command', {
          command: 'set_zoom',
          params: { camera: 'front', factor: val }
      });
  };
  
  const handleLedChange = (mode: string, hexColor: string) => {
      setLedMode(mode);
      setLedColor(hexColor);
      
      // Hex to RGB
      const r = parseInt(hexColor.substr(1,2), 16);
      const g = parseInt(hexColor.substr(3,2), 16);
      const b = parseInt(hexColor.substr(5,2), 16);
      
      socket.emit('control_command', {
          command: 'set_led',
          params: { mode, r, g, b }
      });
  };

  const getVideoUrl = (cam: string) => {
      // Get port from local storage or default to 8000
      const port = localStorage.getItem('robot_port') || '8000';
      return `http://${robotIp}:${port}/api/video/${cam}`;
  };

  return (
    <div className="grid grid-cols-12 gap-4 h-full p-4">
      {/* Left Panel: Camera & Status */}
      <div className="col-span-8 flex flex-col gap-4">
        {/* Video Feeds Grid - Adjusted for Single Camera */}
        <div className="flex-1 bg-black rounded-2xl relative overflow-hidden border border-gray-800 flex items-center justify-center group h-[50vh]">
            <img 
                src={getVideoUrl('front')} 
                className="absolute inset-0 w-full h-full object-contain"
                alt="Front Camera"
                onError={(e) => {e.currentTarget.style.display = 'none'}} 
            />
            <div className="absolute top-4 left-4 bg-black/50 backdrop-blur px-3 py-1 rounded-full text-xs font-mono text-green-400 z-10">
                FRONT CAMERA
            </div>

            {/* Front Cam Zoom Controls Overlay */}
            <div className="absolute bottom-4 left-4 right-4 bg-black/60 backdrop-blur rounded-lg p-2 flex items-center gap-2 z-20 opacity-0 group-hover:opacity-100 transition-opacity max-w-md mx-auto">
                <ZoomIn size={16} className="text-gray-400" />
                <input 
                    type="range" 
                    min="10" max="50" 
                    value={zoomLevel * 10}
                    onChange={(e) => handleZoomChange(parseInt(e.target.value) / 10)}
                    className="flex-1 h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-green-400"
                />
                <span className="text-xs text-white w-8 text-right">{zoomLevel}x</span>
            </div>
        </div>
        
        {/* Sensor Data */}
        <div className="h-48 bg-robot-panel rounded-2xl p-4 grid grid-cols-4 gap-4">
            <div className="bg-gray-800/50 rounded-xl p-3">
                <div className="text-gray-400 text-sm mb-1">Battery</div>
                <div className="text-2xl font-bold text-green-400">{robotState?.battery?.toFixed(1) || 100}%</div>
            </div>
            
            <div className="bg-gray-800/50 rounded-xl p-3 flex flex-col justify-center">
                <div className="flex justify-between items-center mb-2">
                    <span className="text-gray-400 text-xs">FRONT SONAR</span>
                    <span className="text-lg font-bold text-blue-400">
                        {robotState?.sensors?.ultrasonic?.front !== undefined 
                            ? robotState.sensors.ultrasonic.front + ' cm' 
                            : '--'}
                    </span>
                </div>
                <div className="flex justify-between items-center">
                    <span className="text-gray-400 text-xs">REAR SONAR</span>
                    <span className="text-lg font-bold text-yellow-400">
                         {robotState?.sensors?.ultrasonic?.rear !== undefined 
                            ? robotState.sensors.ultrasonic.rear + ' cm' 
                            : '--'}
                    </span>
                </div>
            </div>

             <div className="bg-gray-800/50 rounded-xl p-3">
                <div className="text-gray-400 text-sm mb-1">Infrared (L|C|R)</div>
                <div className="flex gap-2 justify-center mt-2">
                    {robotState?.sensors?.infrared?.map((active: boolean, i: number) => (
                        <div key={i} className={`w-4 h-4 rounded-full ${active ? 'bg-red-500' : 'bg-gray-700'}`} />
                    ))}
                </div>
            </div>
             <div className="bg-gray-800/50 rounded-xl p-3">
                <div className="text-gray-400 text-sm mb-1">Status</div>
                <div className="text-xl font-bold text-white capitalize">{robotState?.status || 'Offline'}</div>
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
             <div className="mb-4 text-xs text-gray-500 font-mono">DIRECTION CONTROL</div>
             
             {/* Arrow Key Pad */}
             <div className="grid grid-cols-3 gap-2 mb-2">
                 {/* Top Row */}
                 <button 
                    onMouseDown={() => handleMove(-1, 1)} onMouseUp={handleStop} onMouseLeave={handleStop}
                    className="p-3 bg-gray-800 hover:bg-gray-700 rounded-lg active:bg-green-600 transition-colors"
                 >
                     <ArrowUp className="-rotate-45" size={24} />
                 </button>
                 <button 
                    onMouseDown={() => handleMove(0, 1)} onMouseUp={handleStop} onMouseLeave={handleStop}
                    className={`p-3 bg-gray-800 hover:bg-gray-700 rounded-lg active:bg-green-600 transition-colors ${activeKeys['ArrowUp'] ? 'bg-green-600' : ''}`}
                 >
                     <ArrowUp size={24} />
                 </button>
                 <button 
                    onMouseDown={() => handleMove(1, 1)} onMouseUp={handleStop} onMouseLeave={handleStop}
                    className="p-3 bg-gray-800 hover:bg-gray-700 rounded-lg active:bg-green-600 transition-colors"
                 >
                     <ArrowUp className="rotate-45" size={24} />
                 </button>

                 {/* Middle Row */}
                 <button 
                    onMouseDown={() => handleMove(-1, 0)} onMouseUp={handleStop} onMouseLeave={handleStop}
                    className={`p-3 bg-gray-800 hover:bg-gray-700 rounded-lg active:bg-green-600 transition-colors ${activeKeys['ArrowLeft'] ? 'bg-green-600' : ''}`}
                 >
                     <ArrowLeft size={24} />
                 </button>
                 <div className="flex items-center justify-center">
                    <div className="w-2 h-2 bg-gray-600 rounded-full" />
                 </div>
                 <button 
                    onMouseDown={() => handleMove(1, 0)} onMouseUp={handleStop} onMouseLeave={handleStop}
                    className={`p-3 bg-gray-800 hover:bg-gray-700 rounded-lg active:bg-green-600 transition-colors ${activeKeys['ArrowRight'] ? 'bg-green-600' : ''}`}
                 >
                     <ArrowRight size={24} />
                 </button>

                 {/* Bottom Row */}
                 <button 
                    onMouseDown={() => handleMove(-1, -1)} onMouseUp={handleStop} onMouseLeave={handleStop}
                    className="p-3 bg-gray-800 hover:bg-gray-700 rounded-lg active:bg-green-600 transition-colors"
                 >
                     <ArrowDown className="rotate-45" size={24} />
                 </button>
                 <button 
                    onMouseDown={() => handleMove(0, -1)} onMouseUp={handleStop} onMouseLeave={handleStop}
                    className={`p-3 bg-gray-800 hover:bg-gray-700 rounded-lg active:bg-green-600 transition-colors ${activeKeys['ArrowDown'] ? 'bg-green-600' : ''}`}
                 >
                     <ArrowDown size={24} />
                 </button>
                 <button 
                    onMouseDown={() => handleMove(1, -1)} onMouseUp={handleStop} onMouseLeave={handleStop}
                    className="p-3 bg-gray-800 hover:bg-gray-700 rounded-lg active:bg-green-600 transition-colors"
                 >
                     <ArrowDown className="-rotate-45" size={24} />
                 </button>
             </div>
             
             <div className="text-[10px] text-gray-500 font-mono">KEYBOARD ARROWS SUPPORTED</div>

            {/* Speed Control */}
            <div className="w-full mt-6 px-4">
                <div className="flex justify-between text-xs text-gray-400 mb-2">
                    <span>SPEED LIMIT</span>
                    <span>{robotState?.speed_limit || 100}%</span>
                </div>
                <input 
                    type="range" 
                    min="0" max="100" 
                    value={robotState?.speed_limit || 100}
                    onChange={(e) => socket.emit('control_command', { 
                        command: 'set_speed', 
                        params: { value: parseInt(e.target.value) } 
                    })}
                    className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-green-500"
                />
            </div>
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

         {/* LED Control */}
         <div className="bg-gray-900/50 rounded-xl p-4 border border-dashed border-gray-800">
            <div className="flex justify-between items-center mb-3">
                <span className="text-xs text-gray-500 font-mono">LED CONTROL</span>
                <input 
                    type="color" 
                    value={ledColor} 
                    onChange={(e) => handleLedChange(ledMode, e.target.value)}
                    className="w-6 h-6 rounded cursor-pointer bg-transparent"
                />
            </div>
            
            <select 
                value={ledMode}
                onChange={(e) => handleLedChange(e.target.value, ledColor)}
                className="w-full bg-gray-700 text-white text-sm rounded p-2 border border-gray-600 focus:outline-none focus:border-blue-500"
            >
                <option value="off">Off</option>
                <option value="static">Static Color</option>
                <option value="blink">Blink</option>
                <option value="breath">Breathing</option>
                <option value="rainbow">Rainbow</option>
                <option value="police">Police Siren</option>
                <option value="ambulance">Ambulance</option>
                <option value="chaser">Chaser</option>
                <option value="fire">Fire</option>
                <option value="color_wipe">Color Wipe</option>
                <option value="theater_chase">Theater Chase</option>
                <option value="strobe">Strobe</option>
                <option value="twinkle">Twinkle</option>
                <option value="sparkle">Sparkle</option>
                <option value="solid_rainbow">Solid Rainbow</option>
                <option value="confetti">Confetti</option>
                <option value="sinelon">Sinelon</option>
                <option value="bpm">BPM</option>
                <option value="juggle">Juggle</option>
                <option value="running_lights">Running Lights</option>
                <option value="meteor">Meteor</option>
                <option value="snow">Snow</option>
                <option value="halloween">Halloween</option>
                <option value="christmas">Christmas</option>
                <option value="usa">USA</option>
                <option value="matrix">Matrix</option>
                <option value="mood">Mood</option>
                <option value="heartbeat">Heartbeat</option>
                <option value="disco">Disco</option>
            </select>
         </div>
        
            {/* AI Actions */}
        <div>
             <h3 className="text-gray-400 text-xs font-bold tracking-wider mb-3">QUICK ACTIONS</h3>
             <div className="grid grid-cols-2 gap-2">
                 <button 
                    onClick={() => socket.emit('control_command', { command: 'track_face' })}
                    className={`p-3 rounded-lg flex items-center justify-center gap-2 transition-colors ${
                        robotState?.status === 'tracking_face' 
                        ? 'bg-blue-600 text-white' 
                        : 'bg-gray-700 hover:bg-gray-600'
                    }`}
                 >
                     <UserCheck size={18} />
                     <span className="text-sm">Track Face</span>
                 </button>
                 
                 <button 
                    onClick={() => socket.emit('control_command', { command: 'line_tracking' })}
                    className={`p-3 rounded-lg flex items-center justify-center gap-2 transition-colors ${
                        robotState?.status === 'line_tracking'
                        ? 'bg-yellow-600 text-white' 
                        : 'bg-gray-700 hover:bg-gray-600'
                    }`}
                 >
                     <Footprints size={18} />
                     <span className="text-sm">Line Track</span>
                 </button>

                 <button 
                    onClick={() => socket.emit('control_command', { command: 'obstacle_avoidance' })}
                    className={`col-span-2 p-3 rounded-lg flex items-center justify-center gap-2 transition-colors ${
                        robotState?.status === 'obstacle_avoidance'
                        ? 'bg-red-600 text-white' 
                        : 'bg-gray-700 hover:bg-gray-600'
                    }`}
                 >
                     <AlertOctagon size={18} />
                     <span className="text-sm">Obstacle Avoidance</span>
                 </button>
                 
                 <button 
                    onClick={() => socket.emit('control_command', { command: 'pickup' })}
                    className={`p-3 rounded-lg flex items-center justify-center gap-2 transition-colors ${
                        robotState?.status?.startsWith('pickup')
                        ? 'bg-green-600 text-white' 
                        : 'bg-gray-700 hover:bg-gray-600'
                    }`}
                 >
                     <Trash2 size={18} />
                     <span className="text-sm">Pickup</span>
                 </button>
                 
                 <button 
                    onClick={() => socket.emit('control_command', { command: 'drop' })}
                    className="p-3 bg-gray-700 hover:bg-gray-600 rounded-lg flex items-center justify-center gap-2 transition-colors"
                 >
                     <RotateCcw size={18} />
                     <span className="text-sm">Drop</span>
                 </button>
             </div>
        </div>

      </div>
    </div>
  );
};

export default Dashboard;