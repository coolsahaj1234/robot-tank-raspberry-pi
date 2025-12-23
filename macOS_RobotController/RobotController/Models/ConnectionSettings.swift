//
//  ConnectionSettings.swift
//  RobotController
//
//  Connection settings model with UserDefaults persistence
//

import Foundation

class ConnectionSettings: ObservableObject {
    @Published var robotIP: String {
        didSet {
            UserDefaults.standard.set(robotIP, forKey: "robotIP")
        }
    }
    
    @Published var commandPort: Int {
        didSet {
            UserDefaults.standard.set(commandPort, forKey: "commandPort")
        }
    }
    
    @Published var videoPort: Int {
        didSet {
            UserDefaults.standard.set(videoPort, forKey: "videoPort")
        }
    }
    
    @Published var autoReconnect: Bool {
        didSet {
            UserDefaults.standard.set(autoReconnect, forKey: "autoReconnect")
        }
    }
    
    init() {
        self.robotIP = UserDefaults.standard.string(forKey: "robotIP") ?? "10.0.0.86"
        self.commandPort = UserDefaults.standard.object(forKey: "commandPort") as? Int ?? 5003
        self.videoPort = UserDefaults.standard.object(forKey: "videoPort") as? Int ?? 8003
        self.autoReconnect = UserDefaults.standard.object(forKey: "autoReconnect") as? Bool ?? true
    }
}

