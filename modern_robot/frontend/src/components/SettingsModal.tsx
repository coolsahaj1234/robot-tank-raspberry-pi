import React, { useState } from 'react';
import { X, Save } from 'lucide-react';
import { updateSocketConnection, getRobotIp, getRobotPort } from '../lib/socket';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUpdate: (ip: string) => void;
}

const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose, onUpdate }) => {
  const [ip, setIp] = useState(getRobotIp());
  const [port, setPort] = useState(getRobotPort());

  if (!isOpen) return null;

  const handleSave = () => {
    updateSocketConnection(ip, port);
    onUpdate(ip);
    onClose();
  };

  return (
    <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
      <div className="bg-robot-panel p-6 rounded-2xl w-96 border border-gray-700 shadow-2xl">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-bold text-white">Connection Settings</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <X size={24} />
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-2">Robot IP Address</label>
            <input
              type="text"
              value={ip}
              onChange={(e) => setIp(e.target.value)}
              placeholder="e.g., 192.168.1.100"
              className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-robot-accent"
            />
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-2">Robot Port</label>
            <input
              type="text"
              value={port}
              onChange={(e) => setPort(e.target.value)}
              placeholder="e.g., 8000"
              className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-robot-accent"
            />
             <p className="text-xs text-gray-500 mt-2">
              Default is 8000.
            </p>
          </div>

          <button
            onClick={handleSave}
            className="w-full bg-robot-accent text-black font-bold py-2 rounded-lg hover:bg-green-400 transition-colors flex items-center justify-center gap-2"
          >
            <Save size={18} />
            Save & Connect
          </button>
        </div>
      </div>
    </div>
  );
};

export default SettingsModal;





