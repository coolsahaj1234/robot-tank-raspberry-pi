# 🚀 START HERE - macOS Robot Controller

## Quick Start (3 Steps)

### ✅ Step 1: Install Xcode (One-Time Setup)

**Xcode is Apple's free development tool - you need it to build Mac apps.**

1. Open **App Store** on your Mac
2. Search **"Xcode"**
3. Click **"Get"** (free, but ~10GB download)
4. Wait for installation (30-60 minutes)
5. Open Xcode once → Accept license

**Verify:** Run `xcodebuild -version` in Terminal

---

### ✅ Step 2: Create Project in Xcode

1. **Open Xcode**
2. **File → New → Project** (`Cmd+Shift+N`)
3. Choose **macOS → App**
4. Fill in:
   - Name: `RobotController`
   - Interface: **SwiftUI** ⚠️
   - Language: **Swift**
5. **IMPORTANT - Save Location:**
   - Navigate **UP one level** to: `/Users/sandeepsingh/Documents/robot-tank-raspberry-pi/`
   - **Save there** (NOT inside macOS_RobotController folder)
   - Xcode will create: `robot-tank-raspberry-pi/RobotController/`
   - ⚠️ **If Xcode asks to move files to trash, click Cancel and save elsewhere!**
6. **Click Create**

---

### ✅ Step 3: Copy Files to Xcode Project

**First, copy files from our source folder:**

1. **In Finder**, go to: `macOS_RobotController/RobotController/`
2. **Copy** these to clipboard:
   - `Models/` folder
   - `Services/` folder
   - `ViewModels/` folder
   - `Views/` folder
   - `Utilities/` folder
   - `RobotControllerApp.swift`
3. **Navigate to:** `robot-tank-raspberry-pi/RobotController/RobotController/`
4. **Paste** all files there

### ✅ Step 4: Add Files to Xcode Project

1. **In Xcode**, right-click `RobotController` folder (blue icon)
2. **"Add Files to RobotController..."**
3. Navigate to: `RobotController/RobotController/` (inside Xcode project)
4. **Select ALL** the folders/files you just pasted
5. **Settings:**
   - ✅ Check "Copy items if needed"
   - ✅ Check "Create groups"
   - ✅ Check "Add to targets: RobotController"
6. **Click Add**

**Then:**
- Select **"My Mac"** as destination
- Press **`⌘R`** to build and run!

---

## 📖 Detailed Instructions

See **INSTALL.md** for complete step-by-step guide with troubleshooting.

## ⚙️ Configuration

The app is **already configured** for your robot:
- **IP:** `10.0.0.86` (your Pi)
- **Command Port:** `5003`
- **Video Port:** `8003`

Just connect and use!

## 🆘 Need Help?

1. **Xcode errors?** → Check INSTALL.md troubleshooting section
2. **Won't connect?** → Verify robot server is running on Pi
3. **Video not showing?** → Check ports 5003/8003 are open

## 🎯 What This App Does

- ✅ Connects to your robot via TCP (ports 5003/8003)
- ✅ Shows live video feed
- ✅ Controls motors (directional pad + keyboard)
- ✅ Controls servos (lift arm, claw)
- ✅ Controls LEDs (color + modes)
- ✅ Shows sensor data (ultrasonic distance)
- ✅ Mode selection (Stop/Move/Sonar/Infrared)

**Ready to go!** Follow the 3 steps above. 🚀

