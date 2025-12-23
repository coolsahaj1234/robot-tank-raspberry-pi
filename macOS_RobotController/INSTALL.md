# macOS Robot Controller - Complete Installation Guide

## Step 1: Install Xcode

Xcode is **required** to build macOS apps. It's free from Apple.

### Installation Steps:

1. **Open the App Store** on your Mac
2. **Search for "Xcode"**
3. **Click "Get"** or "Install" (it's free)
4. **Wait for download** (~10-15 GB, may take 30-60 minutes)
5. **Open Xcode once** after installation
6. **Accept the license agreement** when prompted
7. **Install additional components** if prompted (Command Line Tools)

### Verify Installation:

Open Terminal and run:
```bash
xcodebuild -version
```

You should see something like:
```
Xcode 15.0
Build version 15A240d
```

## Step 2: Create Xcode Project

### Option A: Using Xcode GUI (Recommended)

1. **Open Xcode**
2. **File → New → Project** (or press `Cmd+Shift+N`)
3. **Select "macOS"** tab at the top
4. **Choose "App"** and click **Next**
5. **Fill in the form:**
   - Product Name: `RobotController`
   - Team: (select your Apple ID or "None")
   - Organization Identifier: `com.yourname` (or anything you want)
   - Interface: **SwiftUI** ⚠️ Important!
   - Language: **Swift**
   - Storage: **None** (we'll add files manually)
6. **Click Next**
7. **Navigate to:** `/Users/sandeepsingh/Documents/robot-tank-raspberry-pi/macOS_RobotController`
8. **Click Create**

### Option B: Using Command Line (Advanced)

I'll create a helper script for this - see `setup_project.sh` below.

## Step 3: Add Source Files to Project

**In Xcode:**

1. **Right-click** on the `RobotController` folder (blue icon) in the left sidebar
2. Select **"Add Files to RobotController..."**
3. **Navigate to:** `macOS_RobotController/RobotController/`
4. **Select ALL these folders/files:**
   - `Models/` folder (select the folder, not individual files)
   - `Services/` folder
   - `ViewModels/` folder
   - `Views/` folder
   - `Utilities/` folder
   - `RobotControllerApp.swift` file
5. **Important settings:**
   - ✅ **"Copy items if needed"** - **UNCHECKED**
   - ✅ **"Create groups"** - **SELECTED**
   - ✅ **"Add to targets: RobotController"** - **CHECKED**
6. **Click Add**

## Step 4: Configure Project Settings

1. **Click on "RobotController"** (blue project icon) in the left sidebar
2. **Select the "RobotController" target** (under TARGETS)
3. **General Tab:**
   - Deployment: **macOS 12.0** or later
   - Minimum Deployments: **macOS 12.0**
4. **Signing & Capabilities Tab:**
   - **Uncheck "App Sandbox"** (or add "Outgoing Connections" capability)
   - This allows network access to your robot
5. **Build Settings Tab:**
   - Swift Language Version: **Swift 5** (or latest)

## Step 5: Set Main Entry Point

1. **Find `RobotControllerApp.swift`** in the file list
2. **Right-click** → **"Get Info"**
3. **Target Membership:** Make sure `RobotController` is checked
4. The `@main` attribute should make it the entry point automatically

## Step 6: Build and Run

1. **At the top of Xcode**, select **"My Mac"** as the run destination
2. **Press `⌘R`** (Cmd+R) or click the **Play button** (▶️)
3. **First build may take 1-2 minutes**
4. **The app will launch automatically!**

## Step 7: Configure Connection

When the app launches:

1. **Click the gear icon** (⚙️) in the bottom-left
2. **Verify settings:**
   - Robot IP: `10.0.0.86` (your Pi's IP - already set as default)
   - Command Port: `5003` ✅
   - Video Port: `8003` ✅
3. **Click Save**
4. **Click the WiFi icon** (📶) in the top-left to connect
5. **Status should turn green** when connected
6. **Video feed should appear** automatically

## Troubleshooting

### "Cannot find type in scope" errors
- Make sure all files are added to the target
- Check File Inspector (right panel) → Target Membership

### "Network permission" errors
- Disable App Sandbox in Signing & Capabilities
- Or add "Outgoing Connections" capability

### Build fails with "No such module"
- Clean build folder: Product → Clean Build Folder (Shift+Cmd+K)
- Rebuild: Product → Build (Cmd+B)

### App won't connect
- Verify robot server is running on Pi (ports 5003/8003)
- Check IP address is correct (`10.0.0.86`)
- Make sure Mac and Pi are on same network

### Video not showing
- Check that video port 8003 is accessible
- Verify robot server is sending video stream
- Check firewall settings

## Quick Reference

**Default Settings (already configured):**
- IP: `10.0.0.86`
- Command Port: `5003`
- Video Port: `8003`

**Keyboard Shortcuts:**
- `⌘R` - Build and Run
- `⌘B` - Build only
- `⌘.` - Stop running app

## Need Help?

If you get stuck:
1. Check Xcode's error messages (red icons)
2. Check the console output (bottom panel)
3. Verify all files are in the project
4. Make sure deployment target is macOS 12.0+

