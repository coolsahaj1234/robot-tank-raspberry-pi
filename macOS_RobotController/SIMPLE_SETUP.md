# Simple Setup Guide

## 🎯 Easiest Option: Use the Web Frontend

The React web frontend is already set up and easier to use! Just run:

```bash
cd modern_robot/frontend
npm install  # (only needed first time)
npm run dev
```

Then open http://localhost:5173 in your browser. This gives you a full-featured controller without needing Xcode!

## 🍎 For Native macOS App (Requires Xcode)

If you want the native Mac app, you need Xcode:

### Step 1: Install Xcode
1. Open **App Store** on your Mac
2. Search for **"Xcode"**
3. Click **"Get"** (it's free, but ~10GB download)
4. Wait for installation (can take 30+ minutes)
5. Open Xcode once to accept license

### Step 2: Create Project
1. Open Xcode
2. File → New → Project
3. Choose **macOS** → **App**
4. Click **Next**
5. Fill in:
   - Product Name: `RobotController`
   - Interface: **SwiftUI**
   - Language: **Swift**
6. Click **Next**
7. Save in: `macOS_RobotController` folder
8. Click **Create**

### Step 3: Add Files
1. In Xcode, right-click the `RobotController` folder (blue icon)
2. Select **"Add Files to RobotController..."**
3. Navigate to and select ALL the Swift files:
   - All files in `Models/` folder
   - All files in `Services/` folder  
   - All files in `ViewModels/` folder
   - All files in `Views/` folder
   - All files in `Utilities/` folder
   - `RobotControllerApp.swift`
4. Make sure **"Copy items if needed"** is UNCHECKED
5. Make sure **"Create groups"** is selected
6. Click **Add**

### Step 4: Build & Run
1. At the top of Xcode, select **"My Mac"** as the destination
2. Press **⌘R** (Cmd+R) or click the Play button
3. The app will build and launch!

### Step 5: Configure
1. Click the gear icon in the app
2. Enter your Raspberry Pi IP address
3. Click Save
4. Click the WiFi icon to connect

## 🆘 Troubleshooting

**"Cannot find type in scope" errors:**
- Make sure all files are added to the target (check the file inspector on the right)

**"Network permission" errors:**
- Go to project settings → Signing & Capabilities
- Either disable "App Sandbox" OR add "Outgoing Connections" capability

**Build fails:**
- Make sure deployment target is macOS 12.0 or later
- Check that Swift version is 5.9+

## 💡 Recommendation

**Use the web frontend** (`npm run dev`) - it's:
- ✅ Already working
- ✅ No Xcode needed
- ✅ Same features
- ✅ Works in any browser
- ✅ Easier to update

The native Mac app is nice, but requires Xcode setup. The web version works great!

