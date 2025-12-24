# Debugging Guide

## D-pad Not Working

### Check Browser Console
Look for these messages when clicking D-pad:
- `🎮 D-pad clicked: x=0, y=1, speed=50`
- `📡 Setting manual mode (CMD_MODE#0)` (first time only)
- `📤 Sending motor command: left=50, right=50`
- `📤 Command sent: CMD_MOTOR#50#50`
- `🛑 Stopping motors`
- `📤 Command sent: CMD_MOTOR#0#0`

### If you don't see these messages:
1. Check if `connected` is `true` in React DevTools
2. Check WebSocket connection status
3. Check if buttons are disabled (they should be enabled when connected)

### Check Server Console
Look for:
- `📤 Command: CMD_MODE#0`
- `📤 Command: CMD_MOTOR#50#50`
- `📤 Command: CMD_MOTOR#0#0`

## Video Feed Not Updating

### Check Browser Console
Look for:
- `📹 Received video frame (12345 bytes)` (occasionally)
- `📹 Video frame updated: #30` (every 30 frames)
- `✅ Video frame loaded successfully` (when frames load)

### Check Server Console
Look for:
- `✅ TCP connected to 10.0.0.86:8003` (video socket)
- `📸 Sent video frame #30 (12345 bytes)` (every 30 frames)
- `⚠️ Invalid frame length` (if there are sync issues)
- `⚠️ Frame missing JPEG magic bytes` (if frames are corrupted)

### Common Issues

1. **Video socket not connecting:**
   - Check robot server is running
   - Check port 8003 is accessible: `nc -zv 10.0.0.86 8003`
   - Check firewall settings

2. **Frames not being sent:**
   - Check robot server logs for video thread status
   - Verify camera is working on robot
   - Check robot server is sending frames

3. **Frames received but not displaying:**
   - Check browser console for image load errors
   - Check if `videoFrame` state is updating in React DevTools
   - Try hard refresh (Cmd+Shift+R)

## Quick Tests

### Test D-pad:
1. Open browser console
2. Click a D-pad button
3. Should see: `🎮 D-pad clicked` and `📤 Command sent` messages
4. Check server console for command receipt

### Test Video:
1. Open browser console
2. Connect to robot
3. Should see: `✅ Connected to robot`
4. Watch for: `📹 Received video frame` messages
5. Check server console for: `📸 Sent video frame` messages

## Still Not Working?

1. **Restart everything:**
   - Stop bridge server (Ctrl+C)
   - Restart robot server on Pi
   - Start bridge server: `npm run server`
   - Refresh browser (hard refresh: Cmd+Shift+R)

2. **Check network:**
   - Ping robot: `ping 10.0.0.86`
   - Test ports: `nc -zv 10.0.0.86 5003` and `nc -zv 10.0.0.86 8003`

3. **Check robot server:**
   - Verify robot server is running
   - Check robot server logs for errors
   - Verify camera is working

