//
//  RobotControllerApp.swift
//  RobotController
//
//  Main app entry point
//

import SwiftUI

@main
struct RobotControllerApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
                .frame(minWidth: 1200, minHeight: 800)
        }
        .windowStyle(.hiddenTitleBar)
        .windowToolbarStyle(.unified)
    }
}

