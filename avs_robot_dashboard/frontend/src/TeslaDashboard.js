import React, { Component } from 'react';
import { LogViewer, VIEW_MODE } from 'streetscape.gl';

// AVS Dashboard - Enhanced 3D Visualization

const styles = {
  dashboard: {
    position: 'relative',
    width: '100%',
    height: '100%',
    background: '#000',
    display: 'grid',
    gridTemplateColumns: '280px 1fr 280px',
    gridTemplateRows: '60px 1fr',
    gap: 0,
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
  },
  header: {
    gridColumn: '1 / -1',
    background: 'linear-gradient(180deg, #1a1a1f 0%, #0d0d10 100%)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '0 24px',
    borderBottom: '1px solid #222'
  },
  logo: {
    fontSize: 20,
    fontWeight: 600,
    color: '#fff',
    letterSpacing: 2
  },
  statusBar: {
    display: 'flex',
    alignItems: 'center',
    gap: 20
  },
  statusItem: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    color: '#888',
    fontSize: 13
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: '50%'
  },
  leftPanel: {
    background: '#0d0d10',
    padding: 16,
    display: 'flex',
    flexDirection: 'column',
    gap: 16,
    overflowY: 'auto',
    borderRight: '1px solid #1a1a1f'
  },
  mainView: {
    position: 'relative',
    background: '#000',
    display: 'grid',
    gridTemplateColumns: '1.5fr 1fr',  // Camera 60%, visualizations 40%
    gridTemplateRows: '1fr 1fr',  // Split right side into 2D and 3D
    gap: 8,
    padding: 8
  },
  cameraContainer: {
    position: 'relative',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
    background: '#0a0a0c',
    borderRadius: 12,
    gridRow: '1 / 3'  // Span both rows
  },
  vizMainContainer: {
    position: 'relative',
    overflow: 'hidden',
    background: '#0a0a0c',
    borderRadius: 12,
    minHeight: 300,
    height: '100%',
    display: 'flex',
    flexDirection: 'column'
  },
  cameraFeed: {
    maxWidth: '100%',
    maxHeight: '100%',
    objectFit: 'contain',
    borderRadius: 8
  },
  cameraPlaceholder: {
    color: '#333',
    fontSize: 14,
    textAlign: 'center'
  },
  overlayTop: {
    position: 'absolute',
    top: 16,
    left: '50%',
    transform: 'translateX(-50%)',
    background: 'rgba(0,0,0,0.7)',
    padding: '8px 20px',
    borderRadius: 20,
    display: 'flex',
    alignItems: 'center',
    gap: 12
  },
  speedDisplay: {
    fontSize: 32,
    fontWeight: 300,
    color: '#fff'
  },
  speedUnit: {
    fontSize: 12,
    color: '#666',
    marginLeft: 4
  },
  overlayBottom: {
    position: 'absolute',
    bottom: 16,
    left: '50%',
    transform: 'translateX(-50%)',
    display: 'flex',
    gap: 12
  },
  rightPanel: {
    background: '#0d0d10',
    padding: 16,
    display: 'flex',
    flexDirection: 'column',
    gap: 16,
    overflowY: 'auto',
    borderLeft: '1px solid #1a1a1f'
  },
  card: {
    background: '#151518',
    borderRadius: 12,
    padding: 16,
    border: '1px solid #222'
  },
  cardTitle: {
    fontSize: 11,
    fontWeight: 600,
    color: '#666',
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: 12
  },
  dpad: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 44px)',
    gridTemplateRows: 'repeat(3, 44px)',
    gap: 4,
    justifyContent: 'center'
  },
  dpadBtn: {
    width: 44,
    height: 44,
    border: 'none',
    borderRadius: 8,
    background: '#222',
    color: '#fff',
    fontSize: 16,
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'all 0.1s ease'
  },
  dpadBtnActive: {
    background: '#3b82f6',
    transform: 'scale(0.95)'
  },
  stopBtn: {
    background: '#dc2626',
    fontSize: 10,
    fontWeight: 600
  },
  slider: {
    width: '100%',
    height: 4,
    borderRadius: 2,
    background: '#333',
    outline: 'none',
    cursor: 'pointer',
    marginTop: 8
  },
  sliderLabel: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: 12,
    color: '#888'
  },
  sensorGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: 8
  },
  sensorCard: {
    background: '#1a1a1f',
    borderRadius: 8,
    padding: 12,
    textAlign: 'center'
  },
  sensorLabel: {
    fontSize: 10,
    color: '#666',
    marginBottom: 4
  },
  sensorValue: {
    fontSize: 20,
    fontWeight: 500
  },
  modeSelector: {
    display: 'flex',
    gap: 6,
    flexWrap: 'wrap'
  },
  modeBtn: {
    flex: '1 1 calc(50% - 3px)',
    padding: '10px 8px',
    border: 'none',
    borderRadius: 8,
    background: '#222',
    color: '#888',
    fontSize: 11,
    cursor: 'pointer',
    transition: 'all 0.15s ease'
  },
  modeBtnActive: {
    background: '#3b82f6',
    color: '#fff'
  },
  servoRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8
  },
  servoLabel: {
    width: 40,
    fontSize: 11,
    color: '#888'
  },
  servoValue: {
    width: 30,
    fontSize: 11,
    color: '#3b82f6',
    textAlign: 'right'
  },
  ledColor: {
    width: '100%',
    height: 32,
    border: 'none',
    borderRadius: 6,
    cursor: 'pointer',
    marginBottom: 8
  },
  ledModes: {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, 1fr)',
    gap: 4
  },
  ledModeBtn: {
    padding: '6px 4px',
    border: 'none',
    borderRadius: 4,
    background: '#222',
    color: '#888',
    fontSize: 9,
    cursor: 'pointer'
  },
  vizContainer: {
    height: 250,
    background: '#0a0a0c',
    borderRadius: 8,
    overflow: 'hidden',
    position: 'relative'
  },
  detectionOverlay: {
    position: 'absolute',
    top: 8,
    right: 8,
    background: 'rgba(0,0,0,0.8)',
    padding: '6px 10px',
    borderRadius: 6,
    fontSize: 11,
    color: '#22c55e'
  },
  distanceBar: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    height: 40,
    background: 'linear-gradient(0deg, rgba(0,0,0,0.9) 0%, transparent 100%)',
    display: 'flex',
    justifyContent: 'space-around',
    alignItems: 'center',
    padding: '0 20px'
  },
  distanceIndicator: {
    textAlign: 'center'
  },
  distanceValue: {
    fontSize: 16,
    fontWeight: 500
  },
  distanceLabel: {
    fontSize: 9,
    color: '#666'
  }
};

const MODES = [
  { id: 0, name: 'Stop', icon: '⏹' },
  { id: 1, name: 'Manual', icon: '🎮' },
  { id: 4, name: 'AI Auto', icon: '🤖' },
  { id: 5, name: 'Santa', icon: '🎅' }
];

const LED_MODES = ['Solid', 'Breath', 'Rainbow', 'Chase'];

// Custom 2D Sensor Visualization Component
class SensorVisualization extends Component {
  canvasRef = React.createRef();

  componentDidMount() {
    this.draw();
  }

  componentDidUpdate() {
    this.draw();
  }

  getColor(dist) {
    if (dist < 30) return { fill: 'rgba(255, 0, 0, 0.6)', stroke: '#ff4444' };      // RED - danger
    if (dist < 60) return { fill: 'rgba(255, 140, 0, 0.5)', stroke: '#ff8c00' };    // ORANGE - warning
    if (dist < 100) return { fill: 'rgba(255, 255, 0, 0.4)', stroke: '#ffff00' };   // YELLOW - caution
    return { fill: 'rgba(0, 200, 0, 0.3)', stroke: '#00c800' };                      // GREEN - safe
  }

  draw = () => {
    const canvas = this.canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    const centerX = width / 2;
    const centerY = height / 2;

    // Clear
    ctx.fillStyle = '#0a0a0c';
    ctx.fillRect(0, 0, width, height);

    // Draw grid
    ctx.strokeStyle = '#1a1a1f';
    ctx.lineWidth = 1;
    for (let i = 0; i < width; i += 30) {
      ctx.beginPath();
      ctx.moveTo(i, 0);
      ctx.lineTo(i, height);
      ctx.stroke();
    }
    for (let i = 0; i < height; i += 30) {
      ctx.beginPath();
      ctx.moveTo(0, i);
      ctx.lineTo(width, i);
      ctx.stroke();
    }

    const { frontDist, backDist } = this.props;

    // Scale: 1 meter = 80 pixels, max range 3m
    const scale = 80;
    const maxRange = 2.5 * scale;

    // Draw front sensor cone
    const frontRange = Math.min(Math.max(frontDist / 100, 0.3), 2.5) * scale;
    const frontColor = this.getColor(frontDist);
    this.drawCone(ctx, centerX, centerY - 25, frontRange, -Math.PI / 2, frontColor, 'FRONT');

    // Draw back sensor cone
    const backRange = Math.min(Math.max(backDist / 100, 0.3), 2.5) * scale;
    const backColor = this.getColor(backDist);
    this.drawCone(ctx, centerX, centerY + 25, backRange, Math.PI / 2, backColor, 'BACK');

    // Draw robot body (arrow shape pointing up = forward)
    ctx.save();
    ctx.translate(centerX, centerY);

    // Main body
    ctx.beginPath();
    ctx.moveTo(0, -30);     // Front tip
    ctx.lineTo(20, 0);      // Right side
    ctx.lineTo(20, 25);     // Right back
    ctx.lineTo(-20, 25);    // Left back
    ctx.lineTo(-20, 0);     // Left side
    ctx.closePath();
    ctx.fillStyle = '#4682b4';
    ctx.fill();
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 2;
    ctx.stroke();

    // Front indicator (cyan triangle)
    ctx.beginPath();
    ctx.moveTo(0, -30);
    ctx.lineTo(10, -15);
    ctx.lineTo(-10, -15);
    ctx.closePath();
    ctx.fillStyle = '#00ffff';
    ctx.fill();

    // Back indicator (red bar)
    ctx.fillStyle = '#ff3333';
    ctx.fillRect(-15, 20, 30, 5);

    // Labels
    ctx.fillStyle = '#fff';
    ctx.font = 'bold 10px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('F', 0, -18);
    ctx.fillText('B', 0, 28);

    ctx.restore();

    // Distance labels
    ctx.fillStyle = '#888';
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'center';

    // Draw range circles
    ctx.strokeStyle = '#333';
    ctx.setLineDash([5, 5]);
    [1, 2].forEach(meters => {
      ctx.beginPath();
      ctx.arc(centerX, centerY, meters * scale, 0, Math.PI * 2);
      ctx.stroke();
      ctx.fillText(`${meters}m`, centerX + meters * scale + 15, centerY);
    });
    ctx.setLineDash([]);

    // Distance readouts
    ctx.font = 'bold 14px sans-serif';
    const frontTextColor = this.getColor(frontDist).stroke;
    const backTextColor = this.getColor(backDist).stroke;

    ctx.fillStyle = frontTextColor;
    ctx.fillText(`${frontDist.toFixed(0)} cm`, centerX, 25);

    ctx.fillStyle = backTextColor;
    ctx.fillText(`${backDist.toFixed(0)} cm`, centerX, height - 15);
  }

  drawCone(ctx, x, y, range, angle, color, label) {
    const coneAngle = Math.PI / 4; // 45 degree cone

    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(angle);

    // Draw cone
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.arc(0, 0, range, -coneAngle / 2, coneAngle / 2);
    ctx.closePath();

    ctx.fillStyle = color.fill;
    ctx.fill();
    ctx.strokeStyle = color.stroke;
    ctx.lineWidth = 2;
    ctx.stroke();

    ctx.restore();
  }

  render() {
    return (
      <canvas
        ref={this.canvasRef}
        width={400}
        height={350}
        style={{
          width: '100%',
          height: '100%',
          display: 'block'
        }}
      />
    );
  }
}

class TeslaDashboard extends Component {
  constructor(props) {
    super(props);
    this.state = {
      speed: 60,
      currentMode: 0,
      servo1: 90,
      servo2: 90,
      ledColor: '#3b82f6',
      ledMode: 0,
      activeDirection: null,
      frontDist: 100,
      backDist: 100,
      cameraFrame: null,
      detectedObjects: [],
      imu: { accel: { x: 0, y: 0, z: 0 }, gyro: { x: 0, y: 0, z: 0 } },
      orientation: [0, 0, 0]  // roll, pitch, yaw in radians
    };
  }

  componentDidMount() {
    window.addEventListener('keydown', this.handleKeyDown);
    window.addEventListener('keyup', this.handleKeyUp);
    console.log('🏁 TeslaDashboard mounted - show3DView:', this.props.show3DView, 'xvizLog:', !!this.props.xvizLog);
  }

  componentDidUpdate(prevProps) {
    if (prevProps.show3DView !== this.props.show3DView) {
      console.log('👁️ View changed to:', this.props.show3DView ? '3D' : '2D', 'xvizLog:', !!this.props.xvizLog);
    }
    if (prevProps.xvizLog !== this.props.xvizLog) {
      console.log('📦 xvizLog prop changed:', !!this.props.xvizLog);
    }
  }

  componentWillUnmount() {
    window.removeEventListener('keydown', this.handleKeyDown);
    window.removeEventListener('keyup', this.handleKeyUp);
  }

  sendCommand = (command) => {
    console.log('Dashboard sending:', command);
    if (this.props.onCommand) {
      this.props.onCommand(command);
    }
  };

  calculateMotorSpeeds = (x, y) => {
    const { speed } = this.state;
    const maxSpeed = Math.round(speed * 40.95);
    let leftSpeed = y * maxSpeed + x * maxSpeed * 0.8;
    let rightSpeed = y * maxSpeed - x * maxSpeed * 0.8;
    leftSpeed = Math.max(-4095, Math.min(4095, Math.round(leftSpeed)));
    rightSpeed = Math.max(-4095, Math.min(4095, Math.round(rightSpeed)));
    return { leftSpeed, rightSpeed };
  };

  move = (direction) => {
    this.setState({ activeDirection: direction });
    let x = 0, y = 0;
    switch (direction) {
      case 'forward': y = 1; break;
      case 'backward': y = -1; break;
      case 'left': x = -1; break;
      case 'right': x = 1; break;
      default: break;
    }
    const { leftSpeed, rightSpeed } = this.calculateMotorSpeeds(x, y);
    this.sendCommand(`CMD_MOTOR#${leftSpeed}#${rightSpeed}`);
  };

  stop = () => {
    this.setState({ activeDirection: null });
    this.sendCommand('CMD_MOTOR#0#0');
  };

  handleKeyDown = (e) => {
    if (e.repeat) return;
    const keyMap = {
      'ArrowUp': 'forward', 'w': 'forward',
      'ArrowDown': 'backward', 's': 'backward',
      'ArrowLeft': 'left', 'a': 'left',
      'ArrowRight': 'right', 'd': 'right'
    };
    const direction = keyMap[e.key];
    if (direction) {
      e.preventDefault();
      this.move(direction);
    }
    if (e.key === ' ') {
      e.preventDefault();
      this.stop();
    }
  };

  handleKeyUp = (e) => {
    const keyMap = {
      'ArrowUp': 'forward', 'w': 'forward',
      'ArrowDown': 'backward', 's': 'backward',
      'ArrowLeft': 'left', 'a': 'left',
      'ArrowRight': 'right', 'd': 'right'
    };
    if (keyMap[e.key]) {
      this.stop();
    }
  };

  setMode = (modeId) => {
    this.setState({ currentMode: modeId });
    this.sendCommand(`CMD_MODE#${modeId}`);
  };

  setServo = (index, value) => {
    this.setState({ [index === 0 ? 'servo1' : 'servo2']: value });
    this.sendCommand(`CMD_SERVO#${index}#${value}`);
  };

  setLED = () => {
    const { ledColor, ledMode } = this.state;
    const r = parseInt(ledColor.slice(1, 3), 16);
    const g = parseInt(ledColor.slice(3, 5), 16);
    const b = parseInt(ledColor.slice(5, 7), 16);
    this.sendCommand(`CMD_LED#${ledMode}#${r}#${g}#${b}#100`);
  };

  getDistanceColor = (dist, isFront) => {
    const danger = isFront ? 25 : 20;
    const caution = isFront ? 50 : 40;
    if (dist < danger) return '#ef4444';
    if (dist < caution) return '#f59e0b';
    return '#22c55e';
  };

  render() {
    const {
      speed, currentMode, servo1, servo2, ledColor, ledMode,
      activeDirection, frontDist, backDist, cameraFrame, detectedObjects,
      imu, orientation
    } = this.state;
    const { connected, xvizFrame } = this.props;

    // Extract camera from XVIZ if available
    let cameraImage = cameraFrame;
    if (xvizFrame?.updates?.[0]?.primitives?.['/camera/front']?.images?.[0]?.data) {
      cameraImage = `data:image/jpeg;base64,${xvizFrame.updates[0].primitives['/camera/front'].images[0].data}`;
    }

    return (
      <div style={styles.dashboard}>
        {/* Header */}
        <header style={styles.header}>
          <div style={styles.logo}>ROBOT TANK</div>
          <div style={styles.statusBar}>
            <div style={styles.statusItem}>
              <div style={{ ...styles.statusDot, background: connected ? '#22c55e' : '#ef4444' }} />
              {connected ? 'Connected' : 'Disconnected'}
            </div>
            <div style={styles.statusItem}>
              Mode: {MODES.find(m => m.id === currentMode)?.name || 'Unknown'}
            </div>
          </div>
        </header>

        {/* Left Panel - Controls */}
        <aside style={styles.leftPanel}>
          {/* Mode Selection */}
          <div style={styles.card}>
            <div style={styles.cardTitle}>Drive Mode</div>
            <div style={styles.modeSelector}>
              {MODES.map(mode => (
                <button
                  key={mode.id}
                  style={{
                    ...styles.modeBtn,
                    ...(currentMode === mode.id ? styles.modeBtnActive : {})
                  }}
                  onClick={() => this.setMode(mode.id)}
                >
                  {mode.icon} {mode.name}
                </button>
              ))}
            </div>
          </div>

          {/* Movement D-Pad */}
          <div style={styles.card}>
            <div style={styles.cardTitle}>Manual Control</div>
            <div style={styles.dpad}>
              <div />
              <button
                style={{ ...styles.dpadBtn, ...(activeDirection === 'forward' ? styles.dpadBtnActive : {}) }}
                onMouseDown={() => this.move('forward')}
                onMouseUp={this.stop}
                onMouseLeave={this.stop}
              >▲</button>
              <div />
              <button
                style={{ ...styles.dpadBtn, ...(activeDirection === 'left' ? styles.dpadBtnActive : {}) }}
                onMouseDown={() => this.move('left')}
                onMouseUp={this.stop}
                onMouseLeave={this.stop}
              >◄</button>
              <button
                style={{ ...styles.dpadBtn, ...styles.stopBtn }}
                onClick={this.stop}
              >STOP</button>
              <button
                style={{ ...styles.dpadBtn, ...(activeDirection === 'right' ? styles.dpadBtnActive : {}) }}
                onMouseDown={() => this.move('right')}
                onMouseUp={this.stop}
                onMouseLeave={this.stop}
              >►</button>
              <div />
              <button
                style={{ ...styles.dpadBtn, ...(activeDirection === 'backward' ? styles.dpadBtnActive : {}) }}
                onMouseDown={() => this.move('backward')}
                onMouseUp={this.stop}
                onMouseLeave={this.stop}
              >▼</button>
              <div />
            </div>
            <div style={{ marginTop: 12 }}>
              <div style={styles.sliderLabel}>
                <span>Speed</span>
                <span>{speed}%</span>
              </div>
              <input
                type="range"
                min="10"
                max="100"
                value={speed}
                onChange={(e) => this.setState({ speed: parseInt(e.target.value) })}
                style={styles.slider}
              />
            </div>
          </div>

          {/* Servos */}
          <div style={styles.card}>
            <div style={styles.cardTitle}>Arm Control</div>
            <div style={styles.servoRow}>
              <span style={styles.servoLabel}>Claw</span>
              <input
                type="range"
                min="0"
                max="180"
                value={servo1}
                onChange={(e) => this.setServo(0, parseInt(e.target.value))}
                style={{ ...styles.slider, flex: 1 }}
              />
              <span style={styles.servoValue}>{servo1}°</span>
            </div>
            <div style={styles.servoRow}>
              <span style={styles.servoLabel}>Lift</span>
              <input
                type="range"
                min="0"
                max="180"
                value={servo2}
                onChange={(e) => this.setServo(1, parseInt(e.target.value))}
                style={{ ...styles.slider, flex: 1 }}
              />
              <span style={styles.servoValue}>{servo2}°</span>
            </div>
          </div>
        </aside>

        {/* Main View - Camera + 3D */}
        <main style={styles.mainView}>
          {/* Camera Feed - Top Half */}
          <div style={styles.cameraContainer}>
            {cameraImage ? (
              <img src={cameraImage} alt="Camera Feed" style={styles.cameraFeed} />
            ) : (
              <div style={styles.cameraPlaceholder}>
                <div style={{ fontSize: 48, marginBottom: 8 }}>📷</div>
                <div>Waiting for camera feed...</div>
              </div>
            )}

            {/* Speed Overlay */}
            <div style={styles.overlayTop}>
              <div>
                <span style={styles.speedDisplay}>{speed}</span>
                <span style={styles.speedUnit}>%</span>
              </div>
            </div>

            {/* Detection Overlay */}
            {detectedObjects.length > 0 && (
              <div style={styles.detectionOverlay}>
                {detectedObjects.length} objects detected
              </div>
            )}

            {/* Distance Bar */}
            <div style={styles.distanceBar}>
              <div style={styles.distanceIndicator}>
                <div style={{ ...styles.distanceValue, color: this.getDistanceColor(frontDist, true) }}>
                  {frontDist.toFixed(0)} cm
                </div>
                <div style={styles.distanceLabel}>FRONT</div>
              </div>
              <div style={styles.distanceIndicator}>
                <div style={{ ...styles.distanceValue, color: this.getDistanceColor(backDist, false) }}>
                  {backDist.toFixed(0)} cm
                </div>
                <div style={styles.distanceLabel}>REAR</div>
              </div>
            </div>
          </div>

          {/* 2D Sensor Map - Top Right */}
          <div style={styles.vizMainContainer}>
            <div style={{
              position: 'absolute',
              top: 8,
              left: 8,
              background: 'rgba(0,0,0,0.7)',
              padding: '4px 8px',
              borderRadius: 4,
              fontSize: 11,
              color: '#888',
              zIndex: 50
            }}>
              2D Sensor Map
            </div>
            <div style={{ flex: 1, width: '100%', height: '100%' }}>
              <SensorVisualization
                frontDist={frontDist}
                backDist={backDist}
              />
            </div>
          </div>

          {/* 3D AVS Map - Bottom Right */}
          <div style={styles.vizMainContainer}>
            {this.props.xvizLog && ((() => {
              console.log('🎬 Rendering LogViewer - xvizLog:', this.props.xvizLog);
              return (
              <div style={{
                flex: 1,
                width: '100%',
                height: '100%',
                position: 'relative'
              }}>
                {/* AVS Label */}
                <div style={{
                  position: 'absolute',
                  top: 8,
                  left: 8,
                  background: 'rgba(59, 130, 246, 0.9)',
                  color: 'white',
                  padding: '4px 8px',
                  borderRadius: 4,
                  fontSize: 11,
                  zIndex: 1000,
                  pointerEvents: 'none'
                }}>
                  🗺️ AVS 3D Map
                </div>
                <LogViewer
                  log={this.props.xvizLog}
                  mapStyle="mapbox://styles/mapbox/dark-v9"
                  viewMode={VIEW_MODE.PERSPECTIVE}
                  showMap={false}
                  style={{
                    width: '100%',
                    height: '100%',
                    position: 'absolute',
                    top: 0,
                    left: 0
                  }}
                  streamSettings={{
                    '/vehicle/body': {
                      opacity: 1.0,
                      filled: true,
                      stroked: true,
                      extruded: true,
                      wireframe: false
                    },
                    '/sensors/ultrasonic/front': {
                      opacity: 0.8,
                      filled: true,
                      stroked: true,
                      extruded: true,
                      wireframe: false
                    },
                    '/sensors/ultrasonic/back': {
                      opacity: 0.8,
                      filled: true,
                      stroked: true,
                      extruded: true,
                      wireframe: false
                    },
                    '/objects/detected': {
                      opacity: 0.9,
                      filled: true,
                      stroked: true,
                      extruded: true,
                      wireframe: false
                    },
                    '/ground_plane': {
                      opacity: 0.4,
                      filled: true,
                      stroked: false,
                      extruded: false,
                      wireframe: false
                    }
                  }}
                />
              </div>
              );
            })())}

            {!this.props.xvizLog && (
              <div style={{
                flex: 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#666'
              }}>
                Loading AVS 3D Map...
              </div>
            )}
          </div>
        </main>

        {/* Right Panel - Sensors & LEDs */}
        <aside style={styles.rightPanel}>
          {/* Sensors */}
          <div style={styles.card}>
            <div style={styles.cardTitle}>Proximity Sensors</div>
            <div style={styles.sensorGrid}>
              <div style={styles.sensorCard}>
                <div style={styles.sensorLabel}>Front</div>
                <div style={{ ...styles.sensorValue, color: this.getDistanceColor(frontDist, true) }}>
                  {frontDist.toFixed(0)}
                </div>
                <div style={{ fontSize: 10, color: '#666' }}>cm</div>
              </div>
              <div style={styles.sensorCard}>
                <div style={styles.sensorLabel}>Rear</div>
                <div style={{ ...styles.sensorValue, color: this.getDistanceColor(backDist, false) }}>
                  {backDist.toFixed(0)}
                </div>
                <div style={{ fontSize: 10, color: '#666' }}>cm</div>
              </div>
            </div>
          </div>

          {/* IMU / Gyroscope */}
          <div style={styles.card}>
            <div style={styles.cardTitle}>IMU Sensors</div>
            <div style={{ fontSize: 11, color: '#666', lineHeight: 1.6 }}>
              <div style={{ marginBottom: 8 }}>
                <div style={{ color: '#888', fontSize: 10, marginBottom: 2 }}>GYROSCOPE (rad/s)</div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 4, fontSize: 10 }}>
                  <div>X: <span style={{ color: '#fff' }}>{imu.gyro.x.toFixed(3)}</span></div>
                  <div>Y: <span style={{ color: '#fff' }}>{imu.gyro.y.toFixed(3)}</span></div>
                  <div>Z: <span style={{ color: '#fff' }}>{imu.gyro.z.toFixed(3)}</span></div>
                </div>
              </div>
              <div style={{ marginBottom: 8 }}>
                <div style={{ color: '#888', fontSize: 10, marginBottom: 2 }}>ACCELEROMETER (m/s²)</div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 4, fontSize: 10 }}>
                  <div>X: <span style={{ color: '#fff' }}>{imu.accel.x.toFixed(2)}</span></div>
                  <div>Y: <span style={{ color: '#fff' }}>{imu.accel.y.toFixed(2)}</span></div>
                  <div>Z: <span style={{ color: '#fff' }}>{imu.accel.z.toFixed(2)}</span></div>
                </div>
              </div>
              <div>
                <div style={{ color: '#888', fontSize: 10, marginBottom: 2 }}>ORIENTATION (degrees)</div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 4, fontSize: 10 }}>
                  <div>R: <span style={{ color: '#ff6b6b' }}>{(orientation[0] * 180 / Math.PI).toFixed(1)}°</span></div>
                  <div>P: <span style={{ color: '#4ecdc4' }}>{(orientation[1] * 180 / Math.PI).toFixed(1)}°</span></div>
                  <div>Y: <span style={{ color: '#95e1d3' }}>{(orientation[2] * 180 / Math.PI).toFixed(1)}°</span></div>
                </div>
              </div>
            </div>
          </div>

          {/* LED Control */}
          <div style={styles.card}>
            <div style={styles.cardTitle}>LED Lights</div>
            <input
              type="color"
              value={ledColor}
              onChange={(e) => this.setState({ ledColor: e.target.value }, this.setLED)}
              style={styles.ledColor}
            />
            <div style={styles.ledModes}>
              {LED_MODES.map((mode, i) => (
                <button
                  key={i}
                  style={{
                    ...styles.ledModeBtn,
                    ...(ledMode === i ? { background: ledColor, color: '#fff' } : {})
                  }}
                  onClick={() => this.setState({ ledMode: i }, this.setLED)}
                >
                  {mode}
                </button>
              ))}
            </div>
          </div>

          {/* Quick Stats */}
          <div style={styles.card}>
            <div style={styles.cardTitle}>System Status</div>
            <div style={{ fontSize: 11, color: '#666', lineHeight: 1.8 }}>
              <div>Connection: <span style={{ color: connected ? '#22c55e' : '#ef4444' }}>
                {connected ? 'Active' : 'Lost'}
              </span></div>
              <div>Mode: <span style={{ color: '#3b82f6' }}>
                {MODES.find(m => m.id === currentMode)?.name}
              </span></div>
              <div>Speed: <span style={{ color: '#fff' }}>{speed}%</span></div>
            </div>
          </div>
        </aside>
      </div>
    );
  }
}

export default TeslaDashboard;
