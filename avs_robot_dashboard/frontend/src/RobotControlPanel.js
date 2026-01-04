import React, { Component } from 'react';

// Styles
const styles = {
  panel: {
    position: 'absolute',
    left: 10,
    top: 10,
    bottom: 10,
    width: 320,
    background: 'rgba(20, 20, 25, 0.95)',
    borderRadius: 12,
    padding: 15,
    display: 'flex',
    flexDirection: 'column',
    gap: 15,
    overflowY: 'auto',
    zIndex: 100,
    backdropFilter: 'blur(10px)',
    border: '1px solid rgba(255,255,255,0.1)'
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderBottom: '1px solid rgba(255,255,255,0.1)',
    paddingBottom: 10
  },
  title: {
    fontSize: 18,
    fontWeight: 600,
    color: '#fff',
    margin: 0
  },
  statusDot: {
    width: 10,
    height: 10,
    borderRadius: '50%',
    marginRight: 8
  },
  section: {
    background: 'rgba(255,255,255,0.05)',
    borderRadius: 8,
    padding: 12
  },
  sectionTitle: {
    fontSize: 12,
    color: '#888',
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: 10
  },
  dpad: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 50px)',
    gridTemplateRows: 'repeat(3, 50px)',
    gap: 4,
    justifyContent: 'center',
    margin: '10px 0'
  },
  dpadBtn: {
    width: 50,
    height: 50,
    border: 'none',
    borderRadius: 8,
    background: 'linear-gradient(145deg, #2a2a35, #1a1a22)',
    color: '#fff',
    fontSize: 20,
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'all 0.15s ease',
    boxShadow: '0 2px 8px rgba(0,0,0,0.3)'
  },
  dpadBtnActive: {
    background: 'linear-gradient(145deg, #22c55e, #16a34a)',
    transform: 'scale(0.95)'
  },
  stopBtn: {
    background: 'linear-gradient(145deg, #dc2626, #b91c1c)',
    fontWeight: 'bold',
    fontSize: 12
  },
  sliderContainer: {
    marginTop: 10
  },
  sliderLabel: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: 12,
    color: '#aaa',
    marginBottom: 5
  },
  slider: {
    width: '100%',
    height: 8,
    borderRadius: 4,
    background: '#333',
    outline: 'none',
    cursor: 'pointer'
  },
  modeGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(2, 1fr)',
    gap: 8
  },
  modeBtn: {
    padding: '10px 8px',
    border: 'none',
    borderRadius: 8,
    background: 'rgba(255,255,255,0.1)',
    color: '#fff',
    fontSize: 11,
    cursor: 'pointer',
    transition: 'all 0.15s ease',
    textAlign: 'center'
  },
  modeBtnActive: {
    background: 'linear-gradient(145deg, #22c55e, #16a34a)',
    boxShadow: '0 0 15px rgba(34, 197, 94, 0.3)'
  },
  servoContainer: {
    display: 'flex',
    flexDirection: 'column',
    gap: 12
  },
  servoRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 10
  },
  servoLabel: {
    width: 50,
    fontSize: 12,
    color: '#aaa'
  },
  servoValue: {
    width: 35,
    fontSize: 12,
    color: '#22c55e',
    textAlign: 'right'
  },
  ledContainer: {
    display: 'flex',
    flexDirection: 'column',
    gap: 10
  },
  colorPicker: {
    width: '100%',
    height: 40,
    border: 'none',
    borderRadius: 8,
    cursor: 'pointer',
    background: 'transparent'
  },
  ledModes: {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, 1fr)',
    gap: 6
  },
  ledModeBtn: {
    padding: '8px 4px',
    border: 'none',
    borderRadius: 6,
    background: 'rgba(255,255,255,0.1)',
    color: '#fff',
    fontSize: 10,
    cursor: 'pointer'
  },
  sensorGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(2, 1fr)',
    gap: 10
  },
  sensorCard: {
    background: 'rgba(0,0,0,0.3)',
    borderRadius: 8,
    padding: 10,
    textAlign: 'center'
  },
  sensorLabel: {
    fontSize: 10,
    color: '#888',
    marginBottom: 4
  },
  sensorValue: {
    fontSize: 18,
    fontWeight: 600
  },
  imuGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: 6,
    marginTop: 8
  },
  imuValue: {
    background: 'rgba(0,0,0,0.3)',
    borderRadius: 6,
    padding: 6,
    textAlign: 'center',
    fontSize: 11
  }
};

const MODES = [
  { id: 0, name: 'Stop', icon: '⏹' },
  { id: 1, name: 'Manual', icon: '🎮' },
  { id: 2, name: 'Sonar', icon: '📡' },
  { id: 3, name: 'IR', icon: '🔴' },
  { id: 4, name: 'AI Auto', icon: '🤖' },
  { id: 5, name: 'Santa', icon: '🎅' }
];

const LED_MODES = [
  { id: 0, name: 'Solid' },
  { id: 1, name: 'Breath' },
  { id: 2, name: 'Rainbow' },
  { id: 3, name: 'Chase' }
];

class RobotControlPanel extends Component {
  constructor(props) {
    super(props);
    this.state = {
      speed: 60,
      currentMode: 0,
      servo1: 90,
      servo2: 90,
      ledColor: '#22c55e',
      ledMode: 0,
      ledBrightness: 100,
      activeKeys: new Set(),
      frontDist: 100,
      backDist: 100,
      imu: { accel: { x: 0, y: 0, z: 0 }, gyro: { x: 0, y: 0, z: 0 } }
    };
    this.keydownHandler = this.handleKeyDown.bind(this);
    this.keyupHandler = this.handleKeyUp.bind(this);
  }

  componentDidMount() {
    window.addEventListener('keydown', this.keydownHandler);
    window.addEventListener('keyup', this.keyupHandler);
  }

  componentWillUnmount() {
    window.removeEventListener('keydown', this.keydownHandler);
    window.removeEventListener('keyup', this.keyupHandler);
  }

  sendCommand(command) {
    console.log('Sending command:', command);
    if (this.props.onCommand) {
      this.props.onCommand(command);
    } else {
      console.warn('No onCommand handler provided');
    }
  }

  calculateMotorSpeeds(x, y) {
    const { speed } = this.state;
    const maxSpeed = Math.round(speed * 40.95); // Convert 0-100 to 0-4095

    let leftSpeed = y * maxSpeed + x * maxSpeed * 0.8;
    let rightSpeed = y * maxSpeed - x * maxSpeed * 0.8;

    // Clamp values
    leftSpeed = Math.max(-4095, Math.min(4095, Math.round(leftSpeed)));
    rightSpeed = Math.max(-4095, Math.min(4095, Math.round(rightSpeed)));

    return { leftSpeed, rightSpeed };
  }

  move(direction) {
    console.log('move() called with direction:', direction, 'currentMode:', this.state.currentMode);

    // Auto-switch to Manual mode if not already
    if (this.state.currentMode !== 1) {
      console.log('Auto-switching to Manual mode');
      this.setMode(1);
    }

    let x = 0, y = 0;
    switch (direction) {
      case 'forward': y = 1; break;
      case 'backward': y = -1; break;
      case 'left': x = -1; break;
      case 'right': x = 1; break;
      default: break;
    }
    const { leftSpeed, rightSpeed } = this.calculateMotorSpeeds(x, y);
    console.log('Motor speeds:', leftSpeed, rightSpeed);
    this.sendCommand(`CMD_MOTOR#${leftSpeed}#${rightSpeed}`);
  }

  stop() {
    console.log('stop() called');
    this.sendCommand('CMD_MOTOR#0#0');
  }

  handleKeyDown(e) {
    if (e.repeat || this.state.currentMode !== 1) return;

    const keyMap = {
      'ArrowUp': 'forward',
      'ArrowDown': 'backward',
      'ArrowLeft': 'left',
      'ArrowRight': 'right',
      'w': 'forward',
      's': 'backward',
      'a': 'left',
      'd': 'right'
    };

    const direction = keyMap[e.key];
    if (direction) {
      e.preventDefault();
      this.setState(prev => ({
        activeKeys: new Set([...prev.activeKeys, direction])
      }));
      this.move(direction);
    }

    if (e.key === ' ') {
      e.preventDefault();
      this.stop();
    }
  }

  handleKeyUp(e) {
    const keyMap = {
      'ArrowUp': 'forward',
      'ArrowDown': 'backward',
      'ArrowLeft': 'left',
      'ArrowRight': 'right',
      'w': 'forward',
      's': 'backward',
      'a': 'left',
      'd': 'right'
    };

    const direction = keyMap[e.key];
    if (direction) {
      this.setState(prev => {
        const newKeys = new Set(prev.activeKeys);
        newKeys.delete(direction);
        return { activeKeys: newKeys };
      });
      if (this.state.activeKeys.size <= 1) {
        this.stop();
      }
    }
  }

  setMode(modeId) {
    this.setState({ currentMode: modeId });
    this.sendCommand(`CMD_MODE#${modeId}`);
  }

  setServo(index, value) {
    const stateKey = index === 0 ? 'servo1' : 'servo2';
    this.setState({ [stateKey]: value });
    this.sendCommand(`CMD_SERVO#${index}#${value}`);
  }

  setLED() {
    const { ledColor, ledMode, ledBrightness } = this.state;
    const r = parseInt(ledColor.slice(1, 3), 16);
    const g = parseInt(ledColor.slice(3, 5), 16);
    const b = parseInt(ledColor.slice(5, 7), 16);
    this.sendCommand(`CMD_LED#${ledMode}#${r}#${g}#${b}#${ledBrightness}`);
  }

  getDistanceColor(dist, isFront) {
    const danger = isFront ? 25 : 20;
    const caution = isFront ? 50 : 40;
    if (dist < danger) return '#ef4444';
    if (dist < caution) return '#f59e0b';
    return '#22c55e';
  }

  render() {
    const {
      speed, currentMode, servo1, servo2, ledColor, ledMode, ledBrightness,
      activeKeys, frontDist, backDist, imu
    } = this.state;
    const { connected } = this.props;

    return (
      <div style={styles.panel}>
        {/* Header */}
        <div style={styles.header}>
          <h2 style={styles.title}>Robot Control</h2>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <div style={{
              ...styles.statusDot,
              background: connected ? '#22c55e' : '#ef4444'
            }} />
            <span style={{ fontSize: 12, color: connected ? '#22c55e' : '#ef4444' }}>
              {connected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>

        {/* Mode Selection */}
        <div style={styles.section}>
          <div style={styles.sectionTitle}>Mode</div>
          <div style={styles.modeGrid}>
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

        {/* Movement Controls */}
        <div style={styles.section}>
          <div style={styles.sectionTitle}>Movement (Arrow Keys / WASD)</div>
          <div style={styles.dpad}>
            <div /> {/* Empty cell */}
            <button
              style={{
                ...styles.dpadBtn,
                ...(activeKeys.has('forward') ? styles.dpadBtnActive : {})
              }}
              onMouseDown={() => this.move('forward')}
              onMouseUp={() => this.stop()}
              onMouseLeave={() => this.stop()}
            >
              ▲
            </button>
            <div /> {/* Empty cell */}
            <button
              style={{
                ...styles.dpadBtn,
                ...(activeKeys.has('left') ? styles.dpadBtnActive : {})
              }}
              onMouseDown={() => this.move('left')}
              onMouseUp={() => this.stop()}
              onMouseLeave={() => this.stop()}
            >
              ◄
            </button>
            <button
              style={{ ...styles.dpadBtn, ...styles.stopBtn }}
              onClick={() => this.stop()}
            >
              STOP
            </button>
            <button
              style={{
                ...styles.dpadBtn,
                ...(activeKeys.has('right') ? styles.dpadBtnActive : {})
              }}
              onMouseDown={() => this.move('right')}
              onMouseUp={() => this.stop()}
              onMouseLeave={() => this.stop()}
            >
              ►
            </button>
            <div /> {/* Empty cell */}
            <button
              style={{
                ...styles.dpadBtn,
                ...(activeKeys.has('backward') ? styles.dpadBtnActive : {})
              }}
              onMouseDown={() => this.move('backward')}
              onMouseUp={() => this.stop()}
              onMouseLeave={() => this.stop()}
            >
              ▼
            </button>
            <div /> {/* Empty cell */}
          </div>

          {/* Speed Slider */}
          <div style={styles.sliderContainer}>
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

        {/* Sensors */}
        <div style={styles.section}>
          <div style={styles.sectionTitle}>Sensors</div>
          <div style={styles.sensorGrid}>
            <div style={styles.sensorCard}>
              <div style={styles.sensorLabel}>Front Distance</div>
              <div style={{ ...styles.sensorValue, color: this.getDistanceColor(frontDist, true) }}>
                {frontDist.toFixed(0)} cm
              </div>
            </div>
            <div style={styles.sensorCard}>
              <div style={styles.sensorLabel}>Back Distance</div>
              <div style={{ ...styles.sensorValue, color: this.getDistanceColor(backDist, false) }}>
                {backDist.toFixed(0)} cm
              </div>
            </div>
          </div>

          {/* IMU */}
          <div style={{ marginTop: 10 }}>
            <div style={{ fontSize: 11, color: '#666', marginBottom: 4 }}>Accelerometer (m/s²)</div>
            <div style={styles.imuGrid}>
              <div style={styles.imuValue}>X: {imu.accel.x.toFixed(2)}</div>
              <div style={styles.imuValue}>Y: {imu.accel.y.toFixed(2)}</div>
              <div style={styles.imuValue}>Z: {imu.accel.z.toFixed(2)}</div>
            </div>
          </div>

          {/* Gyroscope */}
          <div style={{ marginTop: 10 }}>
            <div style={{ fontSize: 11, color: '#666', marginBottom: 4 }}>Gyroscope (rad/s)</div>
            <div style={styles.imuGrid}>
              <div style={styles.imuValue}>X: {imu.gyro.x.toFixed(3)}</div>
              <div style={styles.imuValue}>Y: {imu.gyro.y.toFixed(3)}</div>
              <div style={styles.imuValue}>Z: {imu.gyro.z.toFixed(3)}</div>
            </div>
          </div>
        </div>

        {/* Servo Controls */}
        <div style={styles.section}>
          <div style={styles.sectionTitle}>Servos</div>
          <div style={styles.servoContainer}>
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
        </div>

        {/* LED Controls */}
        <div style={styles.section}>
          <div style={styles.sectionTitle}>LED Lights</div>
          <div style={styles.ledContainer}>
            <input
              type="color"
              value={ledColor}
              onChange={(e) => {
                this.setState({ ledColor: e.target.value }, () => this.setLED());
              }}
              style={styles.colorPicker}
            />
            <div style={styles.ledModes}>
              {LED_MODES.map(mode => (
                <button
                  key={mode.id}
                  style={{
                    ...styles.ledModeBtn,
                    ...(ledMode === mode.id ? { background: ledColor, color: '#000' } : {})
                  }}
                  onClick={() => {
                    this.setState({ ledMode: mode.id }, () => this.setLED());
                  }}
                >
                  {mode.name}
                </button>
              ))}
            </div>
            <div style={styles.sliderContainer}>
              <div style={styles.sliderLabel}>
                <span>Brightness</span>
                <span>{ledBrightness}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={ledBrightness}
                onChange={(e) => {
                  this.setState({ ledBrightness: parseInt(e.target.value) }, () => this.setLED());
                }}
                style={styles.slider}
              />
            </div>
          </div>
        </div>
      </div>
    );
  }
}

export default RobotControlPanel;
