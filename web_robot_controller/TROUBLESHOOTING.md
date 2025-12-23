# Troubleshooting Guide

## No Video Feed

### Check Server Console
Look for these messages in the bridge server console:

1. **Connection successful:**
   ```
   ✅ TCP connected to 10.0.0.86:8003
   ```

2. **Video frames being sent:**
   ```
   📸 Sent video frame #30 (12345 bytes)
   ```

3. **If you see errors:**
   ```
   ⚠️ Invalid frame length: [number]
   ⚠️ Frame missing JPEG magic bytes
   ```

### Check Browser Console
Look for these messages:

1. **WebSocket connected:**
   ```
   WebSocket connected
   ✅ Connected to robot
   ```

2. **Video frames received:**
   ```
   📹 Received video frame (12345 bytes)
   ```

### Common Issues

#### 1. Robot Server Not Running
**Symptom:** No TCP connection messages in server console

**Solution:**
- Make sure the robot server is running on Raspberry Pi
- Check IP address is correct
- Verify ports 5003 and 8003 are accessible

#### 2. Video Socket Not Connecting
**Symptom:** Command socket connects but video doesn't

**Solution:**
- Check firewall on Raspberry Pi
- Verify video port (8003) is open
- Check robot server logs for video connection errors

#### 3. Invalid Frame Length Errors
**Symptom:** Server console shows "Invalid frame length"

**Solution:**
- The stream might be out of sync
- Try disconnecting and reconnecting
- Check robot server is sending frames correctly

#### 4. Browser Extension Errors
**Symptom:** "A listener indicated an asynchronous response" error

**Solution:**
- This is usually a browser extension issue, not our code
- Try disabling browser extensions
- Use incognito/private mode

#### 5. 404 Errors
**Symptom:** Failed to load resource: 404

**Solution:**
- These are usually from browser extensions or missing assets
- Check Network tab to see what's failing
- If it's not critical, ignore it

## Debug Steps

1. **Check server is running:**
   ```bash
   # Should see:
   🚀 HTTP server running on http://localhost:3001
   🌐 WebSocket server running on ws://localhost:3002
   ```

2. **Check robot connection:**
   - Click Connect in the web app
   - Watch server console for connection messages
   - Should see: `✅ TCP connected to [IP]:[PORT]`

3. **Check video stream:**
   - After connecting, watch for frame messages
   - Server should log: `📸 Sent video frame #X`
   - Browser should receive frames

4. **Test robot server directly:**
   ```bash
   # On Mac, test TCP connection
   nc -zv 10.0.0.86 8003
   ```

5. **Check robot server logs:**
   - On Raspberry Pi, check if video thread is running
   - Look for connection messages
   - Verify frames are being sent

## Still Not Working?

1. **Restart everything:**
   - Stop bridge server (Ctrl+C)
   - Restart robot server on Pi
   - Start bridge server again
   - Refresh browser

2. **Check network:**
   - Ping robot: `ping 10.0.0.86`
   - Test ports: `nc -zv 10.0.0.86 5003` and `nc -zv 10.0.0.86 8003`

3. **Enable verbose logging:**
   - Check server console for detailed messages
   - Check browser console for WebSocket messages
   - Look for any error patterns

