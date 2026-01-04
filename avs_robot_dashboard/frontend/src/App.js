import React, { Component } from 'react';
import { LogViewer, VIEW_MODE, XVIZLiveLoader } from 'streetscape.gl';
import TeslaDashboard from './TeslaDashboard';

const WS_URL = 'ws://localhost:8081';

class App extends Component {
  state = {
    connected: false,
    robotConnected: false,
    error: null,
    log: null,
    show3DView: true  // Toggle between 2D sensor map and 3D XVIZ - default to 3D for AVS
  };

  ws = null;
  dashboardRef = React.createRef();
  reconnectAttempts = 0;
  maxReconnectAttempts = 10;

  componentDidMount() {
    this.connectWebSocket();
    this.initXVIZLoader();
  }

  initXVIZLoader = () => {
    try {
      console.log('🔧 Initializing XVIZ Loader...');
      const log = new XVIZLiveLoader({
        logGuid: 'mock',
        bufferLength: 30,
        serverConfig: {
          defaultLogLength: 60,
          serverUrl: WS_URL
        },
        worker: false,
        maxConcurrency: 4
      });

      log.on('error', (err) => {
        console.error('❌ XVIZ Loader error:', err);
      });

      log.on('ready', () => {
        console.log('✅ XVIZ Loader ready');
      });

      log.on('update', () => {
        console.log('📊 XVIZ update received');
      });

      log.connect();
      console.log('🔌 XVIZ Loader connecting to:', WS_URL);
      this.setState({ log }, () => {
        console.log('📝 XVIZ log state updated:', !!this.state.log);
      });
    } catch (err) {
      console.error('❌ Failed to init XVIZ:', err);
    }
  };

  componentWillUnmount() {
    if (this.ws) {
      this.ws.close();
    }
  }

  connectWebSocket = () => {
    console.log('Connecting to WebSocket:', WS_URL);
    this.ws = new WebSocket(WS_URL);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.setState({ connected: true, error: null });
      this.reconnectAttempts = 0;
      // Request initial state
      this.ws.send(JSON.stringify({ type: 'robot/get_state' }));
    };

    this.ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        this.handleMessage(msg);
      } catch (e) {
        // Non-JSON message, ignore
      }
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.setState({ connected: false });
      this.scheduleReconnect();
    };

    this.ws.onerror = (err) => {
      console.error('WebSocket error:', err);
      this.setState({ error: 'Connection error' });
    };
  };

  scheduleReconnect = () => {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
      console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
      setTimeout(this.connectWebSocket, delay);
    }
  };

  handleMessage = (msg) => {
    switch (msg.type) {
      case 'robot/state':
        this.setState({
          robotConnected: msg.data?.connected || false
        });
        // Update dashboard sensors including IMU data
        if (this.dashboardRef.current && msg.data?.sensors) {
          const updateState = {
            frontDist: msg.data.sensors.front_distance || 100,
            backDist: msg.data.sensors.back_distance || 100
          };
          // Update IMU data if available
          if (msg.data.sensors.imu) {
            updateState.imu = msg.data.sensors.imu;
          }
          this.dashboardRef.current.setState(updateState);
        }
        break;

      case 'xviz/state_update':
        this.handleXVIZUpdate(msg.data);
        break;

      default:
        break;
    }
  };

  handleXVIZUpdate = (data) => {
    if (!data?.updates?.[0]) return;

    const update = data.updates[0];
    const primitives = update.primitives || {};
    const poses = update.poses || {};

    // Extract camera frame
    const cameraData = primitives['/camera/front']?.images?.[0];
    if (cameraData?.data) {
      const cameraFrame = `data:image/jpeg;base64,${cameraData.data}`;
      if (this.dashboardRef.current) {
        this.dashboardRef.current.setState({ cameraFrame });
      }
    }

    // Extract detected objects
    const objects = primitives['/objects/detected']?.polygons || [];
    if (this.dashboardRef.current && objects.length > 0) {
      this.dashboardRef.current.setState({ detectedObjects: objects });
    }

    // Extract IMU and orientation from vehicle pose
    const vehiclePose = poses['/vehicle_pose'];
    if (vehiclePose && this.dashboardRef.current) {
      const orientation = vehiclePose.orientation || [0, 0, 0];
      this.dashboardRef.current.setState({ orientation });
    }

    // Extract IMU data from variables
    const variables = update.variables || {};
    const imuData = variables['/sensors/imu'];
    if (imuData && this.dashboardRef.current) {
      this.dashboardRef.current.setState({ imu: imuData });
    }
  };

  sendCommand = (command) => {
    console.log('Sending command:', command);
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'robot/command',
        command: command
      }));
    } else {
      console.warn('WebSocket not ready');
    }
  };

  render() {
    const { connected, robotConnected, error } = this.state;

    if (error && !connected) {
      return (
        <div style={{
          width: '100%',
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: '#000',
          color: '#fff',
          flexDirection: 'column',
          gap: 20
        }}>
          <div style={{ fontSize: 48 }}>🤖</div>
          <h1 style={{ margin: 0, fontWeight: 300 }}>Connecting to Robot...</h1>
          <p style={{ color: '#666' }}>Make sure the backend is running on ws://localhost:8081</p>
          <div style={{
            width: 200,
            height: 4,
            background: '#222',
            borderRadius: 2,
            overflow: 'hidden'
          }}>
            <div style={{
              width: '30%',
              height: '100%',
              background: '#3b82f6',
              animation: 'loading 1s infinite ease-in-out'
            }} />
          </div>
          <style>{`
            @keyframes loading {
              0% { transform: translateX(-100%); }
              100% { transform: translateX(400%); }
            }
          `}</style>
        </div>
      );
    }

    const { log, show3DView } = this.state;

    console.log('🎨 Rendering App - show3DView:', show3DView, 'xvizLog:', !!log);

    return (
      <TeslaDashboard
        ref={this.dashboardRef}
        connected={robotConnected}
        onCommand={this.sendCommand}
        show3DView={show3DView}
        onToggleView={() => {
          console.log('🔄 Toggling view from', show3DView, 'to', !show3DView);
          this.setState({ show3DView: !show3DView });
        }}
        xvizLog={log}
      />
    );
  }
}

export default App;
