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

// Store active TCP connections per WebSocket client
const clientConnections = new Map();

/**
 * Create TCP connection to robot server
 */
function createTCPConnection(ip, port, onData, onError, onClose) {
  const socket = new net.Socket();
  
  socket.connect(port, ip, () => {
    console.log(`✅ TCP connected to ${ip}:${port}`);
  });
  
  socket.on('data', (data) => {
    try {
      onData(data);
    } catch (error) {
      console.error('Error in data handler:', error);
    }
  });
  
  socket.on('error', (error) => {
    console.error(`❌ TCP error on ${ip}:${port}:`, error.message);
    onError(error);
  });
  
  socket.on('close', () => {
    console.log(`🔌 TCP disconnected from ${ip}:${port}`);
    onClose();
  });
  
  return socket;
}

/**
 * WebSocket server for real-time communication
 */
const wss = new WebSocket.Server({ port: WS_PORT });

wss.on('connection', (ws, req) => {
  console.log('🌐 New WebSocket client connected');
  
  let commandSocket = null;
  let videoSocket = null;
  let robotIP = DEFAULT_ROBOT_IP;
  let commandPort = DEFAULT_COMMAND_PORT;
  let videoPort = DEFAULT_VIDEO_PORT;
  
  // Video stream state (scoped to this WebSocket connection)
  let videoBuffer = Buffer.alloc(0);
  let expectedFrameLength = null;
  let frameCount = 0;
  
  // Handle messages from browser
  ws.on('message', (message) => {
    try {
      const data = JSON.parse(message.toString());
      
      switch (data.type) {
        case 'connect':
          // Connect to robot server
          robotIP = data.ip || DEFAULT_ROBOT_IP;
          commandPort = data.commandPort || DEFAULT_COMMAND_PORT;
          videoPort = data.videoPort || DEFAULT_VIDEO_PORT;
          
          console.log(`🔌 Connecting to robot at ${robotIP}:${commandPort}/${videoPort}`);
          console.log(`📡 Command socket: ${robotIP}:${commandPort}`);
          console.log(`📹 Video socket: ${robotIP}:${videoPort}`);
          
          // Connect command socket
          commandSocket = createTCPConnection(
            robotIP,
            commandPort,
            (data) => {
              // Forward command responses to browser
              ws.send(JSON.stringify({
                type: 'command_response',
                data: data.toString('utf8')
              }));
            },
            (error) => {
              ws.send(JSON.stringify({
                type: 'error',
                message: `Command socket error: ${error.message}`
              }));
            },
            () => {
              ws.send(JSON.stringify({ type: 'disconnected', socket: 'command' }));
            }
          );
          
          // Connect video socket with frame length parsing
          // Reset video buffer state for new connection
          videoBuffer = Buffer.alloc(0);
          expectedFrameLength = null;
          frameCount = 0;
          
          console.log(`📹 Initializing video stream buffer for ${robotIP}:${videoPort}`);
          
          videoSocket = createTCPConnection(
            robotIP,
            videoPort,
            (data) => {
              try {
                // Accumulate data in buffer
                videoBuffer = Buffer.concat([videoBuffer, data]);
                
                // Process buffer continuously
                while (videoBuffer.length > 0) {
                  if (expectedFrameLength === null) {
                    // Waiting for 4-byte length header
                    if (videoBuffer.length >= 4) {
                      // Parse little-endian UInt32
                      expectedFrameLength = videoBuffer.readUInt32LE(0);
                      videoBuffer = videoBuffer.slice(4);
                      
                      // Validate frame length (1KB to 5MB)
                      if (expectedFrameLength < 1000 || expectedFrameLength > 5000000) {
                        console.warn(`⚠️ Invalid frame length: ${expectedFrameLength}, resyncing...`);
                        // Try to find JPEG magic bytes
                        const jpegMagic = Buffer.from([0xFF, 0xD8, 0xFF]);
                        const magicIndex = videoBuffer.indexOf(jpegMagic);
                        if (magicIndex >= 0) {
                          videoBuffer = videoBuffer.slice(magicIndex);
                        } else {
                          // Keep last 3 bytes in case magic is split
                          videoBuffer = videoBuffer.slice(-3);
                        }
                        expectedFrameLength = null;
                        continue;
                      }
                      
                      // Valid length, continue to read frame
                    } else {
                      break; // Need more data for length header
                    }
                  }
                  
                  if (expectedFrameLength !== null) {
                    // Waiting for frame data
                    if (videoBuffer.length >= expectedFrameLength) {
                      // Extract frame
                      const frameData = videoBuffer.slice(0, expectedFrameLength);
                      videoBuffer = videoBuffer.slice(expectedFrameLength);
                      
                      // Verify JPEG magic bytes
                      if (frameData.length >= 3 && 
                          frameData[0] === 0xFF && 
                          frameData[1] === 0xD8 && 
                          frameData[2] === 0xFF) {
                        // Forward video frame to browser as base64
                        const base64 = frameData.toString('base64');
                        if (ws.readyState === WebSocket.OPEN) {
                          frameCount++;
                          if (frameCount % 30 === 0) {
                            console.log(`📸 Sent video frame #${frameCount} (${frameData.length} bytes)`);
                          }
                          ws.send(JSON.stringify({
                            type: 'video_frame',
                            data: base64,
                            length: frameData.length
                          }));
                        }
                      } else {
                        console.warn('⚠️ Frame missing JPEG magic bytes, skipping');
                      }
                      
                      expectedFrameLength = null;
                    } else {
                      break; // Need more data for frame
                    }
                  }
                }
              } catch (error) {
                console.error('❌ Error processing video data:', error);
                // Reset on error
                videoBuffer = Buffer.alloc(0);
                expectedFrameLength = null;
              }
            },
            (error) => {
              ws.send(JSON.stringify({
                type: 'error',
                message: `Video socket error: ${error.message}`
              }));
            },
            () => {
              ws.send(JSON.stringify({ type: 'disconnected', socket: 'video' }));
            }
          );
          
          ws.send(JSON.stringify({ type: 'connected' }));
          break;
          
        case 'command':
          // Send command to robot
          if (commandSocket && commandSocket.writable) {
            const command = data.command + '\n';
            commandSocket.write(command, 'utf8');
            console.log(`📤 Command: ${data.command}`);
          } else {
            ws.send(JSON.stringify({
              type: 'error',
              message: 'Not connected to robot'
            }));
          }
          break;
          
        case 'disconnect':
          // Disconnect from robot
          if (commandSocket) {
            commandSocket.destroy();
            commandSocket = null;
          }
          if (videoSocket) {
            videoSocket.destroy();
            videoSocket = null;
          }
          ws.send(JSON.stringify({ type: 'disconnected' }));
          break;
          
        default:
          console.warn('Unknown message type:', data.type);
      }
    } catch (error) {
      console.error('Error handling WebSocket message:', error);
      ws.send(JSON.stringify({
        type: 'error',
        message: error.message
      }));
    }
  });
  
  ws.on('close', () => {
    console.log('🌐 WebSocket client disconnected');
    if (commandSocket) {
      commandSocket.destroy();
    }
    if (videoSocket) {
      videoSocket.destroy();
    }
    clientConnections.delete(ws);
  });
  
  ws.on('error', (error) => {
    console.error('WebSocket error:', error);
  });
  
  // Send initial connection status
  ws.send(JSON.stringify({
    type: 'ready',
    message: 'WebSocket server ready'
  }));
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

// Start HTTP server
app.listen(PORT, () => {
  console.log(`🚀 HTTP server running on http://localhost:${PORT}`);
  console.log(`🌐 WebSocket server running on ws://localhost:${WS_PORT}`);
  console.log(`📡 Ready to bridge connections to robot server`);
  console.log(`\n💡 Make sure your robot server is running on the Raspberry Pi`);
  console.log(`💡 Default robot IP: ${DEFAULT_ROBOT_IP}:${DEFAULT_COMMAND_PORT}/${DEFAULT_VIDEO_PORT}\n`);
});

