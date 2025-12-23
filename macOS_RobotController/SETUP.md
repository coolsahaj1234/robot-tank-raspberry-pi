# Setup Instructions

## Creating the Xcode Project

Since Xcode project files are complex binary/XML formats, you'll need to create the project in Xcode:

1. **Open Xcode** and select "Create a new Xcode project"

2. **Choose template**:
   - Platform: macOS
   - Application Type: App
   - Interface: SwiftUI
   - Language: Swift
   - Name: `RobotController`
   - Organization Identifier: `com.yourname` (or your preferred identifier)
   - Bundle Identifier: `com.yourname.RobotController`

3. **Save the project** in the `macOS_RobotController` directory (replace the auto-generated folder)

4. **Add existing files**:
   - Right-click on the `RobotController` folder in Xcode
   - Select "Add Files to RobotController..."
   - Navigate to and select all the Swift files:
     - Models/ (RobotCommand.swift, RobotState.swift, ConnectionSettings.swift)
     - Services/ (TCPConnectionManager.swift, CommandService.swift, VideoStreamService.swift)
     - ViewModels/ (RobotViewModel.swift)
     - Views/ (all .swift files)
     - Utilities/ (CommandBuilder.swift)
   - Make sure "Copy items if needed" is **unchecked**
   - Make sure "Create groups" is selected
   - Click "Add"

5. **Configure project settings**:
   - Select the project in the navigator
   - Under "Deployment Info":
     - Set macOS deployment target to **12.0** or later
   - Under "Signing & Capabilities":
     - Enable "App Sandbox" if you want sandboxing, but you'll need to add:
       - Outgoing Connections (Client)
       - Incoming Connections (Server) - if needed
     - OR disable App Sandbox for full network access
   - Under "Build Settings":
     - Ensure Swift Language Version is **Swift 5** or later

6. **Set the app entry point**:
   - Make sure `RobotControllerApp.swift` is set as the main entry point
   - In the project settings, under "General" → "Deployment Info", ensure the main interface is set correctly

7. **Build and run**:
   - Select "My Mac" as the run destination
   - Press Cmd+R to build and run

## Alternative: Command Line Setup

If you prefer, you can use Xcode's command-line tools:

```bash
cd macOS_RobotController
# Create a basic project structure (you'll still need to configure in Xcode)
```

## Troubleshooting

### Network Issues
- If you get network permission errors, disable App Sandbox or add network capabilities
- Make sure the robot server is running on the Raspberry Pi
- Check firewall settings on both Mac and Raspberry Pi

### Build Errors
- Ensure all files are added to the target
- Check that Swift version is compatible (5.9+)
- Verify all imports are correct

### Runtime Issues
- Check console for connection errors
- Verify IP address and ports in Settings
- Ensure robot server is accessible on the network

## Project Structure

```
macOS_RobotController/
├── RobotController/
│   ├── RobotControllerApp.swift
│   ├── Models/
│   │   ├── RobotCommand.swift
│   │   ├── RobotState.swift
│   │   └── ConnectionSettings.swift
│   ├── Services/
│   │   ├── TCPConnectionManager.swift
│   │   ├── CommandService.swift
│   │   └── VideoStreamService.swift
│   ├── ViewModels/
│   │   └── RobotViewModel.swift
│   ├── Views/
│   │   ├── ContentView.swift
│   │   ├── DashboardView.swift
│   │   ├── VideoView.swift
│   │   ├── ControlPanelView.swift
│   │   ├── LEDControlView.swift
│   │   ├── ModeSelectorView.swift
│   │   ├── SensorDataView.swift
│   │   └── SettingsView.swift
│   └── Utilities/
│       └── CommandBuilder.swift
└── README.md
```

