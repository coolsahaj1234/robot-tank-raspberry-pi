#!/usr/bin/env node
/**
 * Bridge Server: WebSocket/HTTP -> TCP (old_robot server)
 * Connects browser clients to the old_robot TCP server
 */

const express = require('express');
const WebSocket = require('ws');
const net = require('net');
const cors = require('cors');
const path = require('path');

const app = express();
app.use(cors());
app.use(express.json());

// Serve static files from React build (for production)
app.use(express.static(path.join(__dirname, '../client/dist')));

const PORT = 3001;
const WS_PORT = 3002;

// Default robot server settings
const DEFAULT_ROBOT_IP = '10.0.0.86';
const DEFAULT_COMMAND_PORT = 5003;
const DEFAULT_VIDEO_PORT = 8003;

// TCP connection timeout
const TCP_CONNECT_TIMEOUT = 5000;

/**
 * Create TCP connection to robot server with timeout
 */
function createTCPConnection(ip, port, onConnect, onData, onError, onClose) {
  const socket = new net.Socket();
  let connected = false;
  let connectTimeout = null;

  // Set connection timeout
  connectTimeout = setTimeout(() => {
    if (!connected) {
      console.error(`❌ TCP connection timeout to ${ip}:${port}`);
      socket.destroy();
      onError(new Error(`Connection timeout to ${ip}:${port}`));
    }
  }, TCP_CONNECT_TIMEOUT);

  socket.connect(port, ip, () => {
    connected = true;
    clearTimeout(connectTimeout);
    console.log(`✅ TCP connected to ${ip}:${port}`);
    onConnect();
  });

  socket.on('data', (data) => {
    try {
      onData(data);
    } catch (error) {
      console.error('Error in data handler:', error);
    }
  });

  socket.on('error', (error) => {
    clearTimeout(connectTimeout);
    console.error(`❌ TCP error on ${ip}:${port}:`, error.message);
    onError(error);
  });

  socket.on('close', () => {
    clearTimeout(connectTimeout);
    console.log(`🔌 TCP disconnected from ${ip}:${port}`);
    onClose();
  });

  return socket;
}

/**
 * Safely destroy a socket
 */
function destroySocket(socket) {
  if (socket) {
    try {
      socket.removeAllListeners();
      socket.destroy();
    } catch (e) {
      // Ignore errors during cleanup
    }
  }
  return null;
}

// WebSocket server for real-time communication - bind to 0.0.0.0 for LAN access
const wss = new WebSocket.Server({ port: WS_PORT, host: '0.0.0.0' });

wss.on('error', (err) => {
  console.error('❌ WebSocket server error:', err.message);
});

wss.on('connection', (ws, req) => {
  const clientIP = req.socket.remoteAddress;
  console.log(`🌐 New WebSocket client connected from ${clientIP}`);

  let commandSocket = null;
  let videoSocket = null;
  let robotIP = DEFAULT_ROBOT_IP;
  let commandPort = DEFAULT_COMMAND_PORT;
  let videoPort = DEFAULT_VIDEO_PORT;
  let isConnecting = false;
  let robotConnected = false;

  // Video stream state
  let videoBuffer = Buffer.alloc(0);
  let expectedFrameLength = null;
  let frameCount = 0;

  // Cleanup function
  const cleanupRobotConnection = () => {
    commandSocket = destroySocket(commandSocket);
    videoSocket = destroySocket(videoSocket);
    videoBuffer = Buffer.alloc(0);
    expectedFrameLength = null;
    frameCount = 0;
    robotConnected = false;
    isConnecting = false;
  };

  // Send message safely
  const safeSend = (data) => {
    if (ws.readyState === WebSocket.OPEN) {
      try {
        ws.send(JSON.stringify(data));
      } catch (e) {
        console.error('Error sending WebSocket message:', e);
      }
    }
  };

  // Handle messages from browser
  ws.on('message', (message) => {
    try {
      const data = JSON.parse(message.toString());

      switch (data.type) {
        case 'connect':
          // Clean up any existing connections first
          cleanupRobotConnection();

          robotIP = data.ip || DEFAULT_ROBOT_IP;
          commandPort = data.commandPort || DEFAULT_COMMAND_PORT;
          videoPort = data.videoPort || DEFAULT_VIDEO_PORT;
          isConnecting = true;

          console.log(`🔌 Connecting to robot at ${robotIP}:${commandPort}/${videoPort}`);

          let commandConnected = false;
          let videoConnected = false;
          let connectionFailed = false;

          const checkAllConnected = () => {
            if (connectionFailed) return;
            if (commandConnected && videoConnected) {
              robotConnected = true;
              isConnecting = false;
              safeSend({ type: 'connected' });
              console.log(`✅ Fully connected to robot at ${robotIP}`);
            }
          };

          const handleConnectionError = (socketType, error) => {
            if (connectionFailed) return;
            connectionFailed = true;
            isConnecting = false;
            console.error(`❌ ${socketType} connection failed: ${error.message}`);
            cleanupRobotConnection();
            safeSend({
              type: 'connection_failed',
              message: `${socketType} connection failed: ${error.message}`,
              canRetry: true
            });
          };

          // Connect command socket
          commandSocket = createTCPConnection(
            robotIP,
            commandPort,
            () => {
              commandConnected = true;
              checkAllConnected();
            },
            (data) => {
              safeSend({
                type: 'command_response',
                data: data.toString('utf8')
              });
            },
            (error) => handleConnectionError('Command', error),
            () => {
              if (robotConnected) {
                safeSend({ type: 'disconnected', socket: 'command' });
                cleanupRobotConnection();
              }
            }
          );

          // Connect video socket
          videoSocket = createTCPConnection(
            robotIP,
            videoPort,
            () => {
              videoConnected = true;
              checkAllConnected();
            },
            (data) => {
              try {
                videoBuffer = Buffer.concat([videoBuffer, data]);

                while (videoBuffer.length > 0) {
                  if (expectedFrameLength === null) {
                    if (videoBuffer.length >= 4) {
                      expectedFrameLength = videoBuffer.readUInt32LE(0);
                      videoBuffer = videoBuffer.slice(4);

                      if (expectedFrameLength < 1000 || expectedFrameLength > 5000000) {
                        const jpegMagic = Buffer.from([0xFF, 0xD8, 0xFF]);
                        const magicIndex = videoBuffer.indexOf(jpegMagic);
                        if (magicIndex >= 0) {
                          videoBuffer = videoBuffer.slice(magicIndex);
                        } else {
                          videoBuffer = videoBuffer.slice(-3);
                        }
                        expectedFrameLength = null;
                        continue;
                      }
                    } else {
                      break;
                    }
                  }

                  if (expectedFrameLength !== null) {
                    if (videoBuffer.length >= expectedFrameLength) {
                      const frameData = videoBuffer.slice(0, expectedFrameLength);
                      videoBuffer = videoBuffer.slice(expectedFrameLength);

                      if (frameData.length >= 3 &&
                        frameData[0] === 0xFF &&
                        frameData[1] === 0xD8 &&
                        frameData[2] === 0xFF) {
                        const base64 = frameData.toString('base64');
                        frameCount++;
                        if (frameCount % 30 === 0) {
                          console.log(`📸 Sent frame #${frameCount} (${frameData.length} bytes)`);
                        }
                        safeSend({
                          type: 'video_frame',
                          data: base64,
                          length: frameData.length
                        });
                      }
                      expectedFrameLength = null;
                    } else {
                      break;
                    }
                  }
                }
              } catch (error) {
                console.error('❌ Error processing video:', error);
                videoBuffer = Buffer.alloc(0);
                expectedFrameLength = null;
              }
            },
            (error) => handleConnectionError('Video', error),
            () => {
              if (robotConnected) {
                safeSend({ type: 'disconnected', socket: 'video' });
                cleanupRobotConnection();
              }
            }
          );
          break;

        case 'command':
          if (commandSocket && commandSocket.writable && robotConnected) {
            const command = data.command + '\n';
            commandSocket.write(command, 'utf8');
          } else {
            safeSend({
              type: 'error',
              message: 'Not connected to robot'
            });
          }
          break;

        case 'disconnect':
          cleanupRobotConnection();
          safeSend({ type: 'disconnected' });
          break;

        case 'ping':
          safeSend({ type: 'pong', timestamp: Date.now() });
          break;

        default:
          console.warn('Unknown message type:', data.type);
      }
    } catch (error) {
      console.error('Error handling WebSocket message:', error);
      safeSend({
        type: 'error',
        message: error.message
      });
    }
  });

  ws.on('close', () => {
    console.log(`🌐 WebSocket client disconnected from ${clientIP}`);
    cleanupRobotConnection();
  });

  ws.on('error', (error) => {
    console.error('WebSocket error:', error);
  });

  // Send initial ready message
  safeSend({
    type: 'ready',
    message: 'WebSocket server ready'
  });
});

// HTTP API endpoints
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Fallback to React app for all other routes (only in production)
if (process.env.NODE_ENV === 'production') {
  app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, '../client/dist/index.html'));
  });
}

// Start HTTP server - bind to 0.0.0.0 for LAN access
app.listen(PORT, '0.0.0.0', () => {
  console.log(`🚀 HTTP server running on http://0.0.0.0:${PORT}`);
  console.log(`🌐 WebSocket server running on ws://0.0.0.0:${WS_PORT}`);
  console.log(`📡 Ready to bridge connections to robot server`);
  console.log(`\n💡 Make sure your robot server is running on the Raspberry Pi`);
  console.log(`💡 Default robot IP: ${DEFAULT_ROBOT_IP}:${DEFAULT_COMMAND_PORT}/${DEFAULT_VIDEO_PORT}\n`);
});
