//
//  RobotViewModel.swift
//  RobotController
//
//  Main view model managing app state and robot control
//

import Foundation
import SwiftUI
import Combine

class RobotViewModel: ObservableObject {
    @Published var robotState = RobotState()
    @Published var connectionSettings = ConnectionSettings()
    @Published var currentVideoFrame: NSImage?
    
    private let connectionManager = TCPConnectionManager()
    private let commandService: CommandService
    private let videoService: VideoStreamService
    private var cancellables = Set<AnyCancellable>()
    
    // Keyboard state tracking
    private var pressedKeys: Set<String> = []
    
    init() {
        commandService = CommandService(connectionManager: connectionManager)
        videoService = VideoStreamService(connectionManager: connectionManager)
        
        connectionManager.delegate = self
        videoService.delegate = self
        
        setupKeyboardMonitoring()
    }
    
    func connect() {
        connectionManager.connect(
            ip: connectionSettings.robotIP,
            commandPort: connectionSettings.commandPort,
            videoPort: connectionSettings.videoPort
        )
    }
    
    func disconnect() {
        videoService.stopReceiving()
        connectionManager.disconnect()
        stopMotors()
    }
    
    // MARK: - Motor Control
    
    func move(x: Double, y: Double) {
        let speed = Double(robotState.speedLimit)
        let leftSpeed = Int((y * speed) + (x * speed * 0.5))
        let rightSpeed = Int((y * speed) - (x * speed * 0.5))
        
        let clampedLeft = max(-100, min(100, leftSpeed))
        let clampedRight = max(-100, min(100, rightSpeed))
        
        robotState.leftMotorSpeed = clampedLeft
        robotState.rightMotorSpeed = clampedRight
        
        commandService.sendMotorCommand(leftSpeed: clampedLeft, rightSpeed: clampedRight)
    }
    
    func stopMotors() {
        robotState.leftMotorSpeed = 0
        robotState.rightMotorSpeed = 0
        commandService.sendMotorCommand(leftSpeed: 0, rightSpeed: 0)
    }
    
    // MARK: - Servo Control
    
    func setServo1Angle(_ angle: Int) {
        robotState.servo1Angle = angle
        commandService.sendServoCommand(index: 0, angle: angle)
    }
    
    func setServo2Angle(_ angle: Int) {
        robotState.servo2Angle = angle
        commandService.sendServoCommand(index: 1, angle: angle)
    }
    
    // MARK: - LED Control
    
    func setLED(mode: LEDMode, color: Color) {
        robotState.ledMode = mode
        robotState.ledColor = color
        
        let components = color.cgColor?.components ?? [0, 1, 0, 1]
        let r = Int(components[0] * 255)
        let g = Int(components[1] * 255)
        let b = Int(components[2] * 255)
        
        robotState.ledR = r
        robotState.ledG = g
        robotState.ledB = b
        
        commandService.sendLEDCommand(mode: mode, r: r, g: g, b: b)
    }
    
    // MARK: - Mode Control
    
    func setMode(_ mode: RobotMode) {
        robotState.currentMode = mode
        commandService.sendModeCommand(mode: mode)
    }
    
    // MARK: - Action Control
    
    func performAction(_ action: RobotAction) {
        commandService.sendActionCommand(action: action)
    }
    
    // MARK: - Keyboard Handling
    
    private func setupKeyboardMonitoring() {
        NSEvent.addLocalMonitorForEvents(matching: .keyDown) { [weak self] event in
            self?.handleKeyDown(event)
            return event
        }
        
        NSEvent.addLocalMonitorForEvents(matching: .keyUp) { [weak self] event in
            self?.handleKeyUp(event)
            return event
        }
    }
    
    private func handleKeyDown(_ event: NSEvent) {
        guard robotState.isConnected else { return }
        
        let key = event.keyCode
        var keyName: String?
        
        switch key {
        case 126: keyName = "ArrowUp"
        case 125: keyName = "ArrowDown"
        case 123: keyName = "ArrowLeft"
        case 124: keyName = "ArrowRight"
        default: break
        }
        
        if let keyName = keyName, !pressedKeys.contains(keyName) {
            pressedKeys.insert(keyName)
            updateMovementFromKeys()
        }
    }
    
    private func handleKeyUp(_ event: NSEvent) {
        guard robotState.isConnected else { return }
        
        let key = event.keyCode
        var keyName: String?
        
        switch key {
        case 126: keyName = "ArrowUp"
        case 125: keyName = "ArrowDown"
        case 123: keyName = "ArrowLeft"
        case 124: keyName = "ArrowRight"
        default: break
        }
        
        if let keyName = keyName {
            pressedKeys.remove(keyName)
            updateMovementFromKeys()
        }
    }
    
    private func updateMovementFromKeys() {
        var x: Double = 0
        var y: Double = 0
        
        if pressedKeys.contains("ArrowUp") { y += 1.0 }
        if pressedKeys.contains("ArrowDown") { y -= 1.0 }
        if pressedKeys.contains("ArrowLeft") { x -= 1.0 }
        if pressedKeys.contains("ArrowRight") { x += 1.0 }
        
        if x == 0 && y == 0 {
            stopMotors()
        } else {
            move(x: x, y: y)
        }
    }
}

// MARK: - TCPConnectionManagerDelegate

extension RobotViewModel: TCPConnectionManagerDelegate {
    func didReceiveCommandResponse(_ message: String) {
        if let distance = CommandBuilder.parseSonicResponse(message) {
            DispatchQueue.main.async {
                self.robotState.ultrasonicDistance = distance
            }
        }
    }
    
    func didUpdateConnectionStatus(_ isConnected: Bool) {
        DispatchQueue.main.async {
            self.robotState.isConnected = isConnected
            if isConnected {
                self.videoService.startReceiving()
            } else {
                self.videoService.stopReceiving()
                self.stopMotors()
            }
        }
    }
}

// MARK: - VideoStreamServiceDelegate

extension RobotViewModel: VideoStreamServiceDelegate {
    func didReceiveVideoFrame(_ image: NSImage) {
        DispatchQueue.main.async {
            self.currentVideoFrame = image
        }
    }
}

