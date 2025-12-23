//
//  CommandService.swift
//  RobotController
//
//  Command sending service
//

import Foundation

class CommandService {
    private let connectionManager: TCPConnectionManager
    
    init(connectionManager: TCPConnectionManager) {
        self.connectionManager = connectionManager
    }
    
    func sendMotorCommand(leftSpeed: Int, rightSpeed: Int) {
        let command = CommandBuilder.buildMotorCommand(leftSpeed: leftSpeed, rightSpeed: rightSpeed)
        connectionManager.sendCommand(command)
    }
    
    func sendServoCommand(index: Int, angle: Int) {
        let command = CommandBuilder.buildServoCommand(index: index, angle: angle)
        connectionManager.sendCommand(command)
    }
    
    func sendLEDCommand(mode: LEDMode, r: Int, g: Int, b: Int, index: Int = 15) {
        let command = CommandBuilder.buildLEDCommand(mode: mode, r: r, g: g, b: b, index: index)
        connectionManager.sendCommand(command)
    }
    
    func sendModeCommand(mode: RobotMode) {
        let command = CommandBuilder.buildModeCommand(mode: mode)
        connectionManager.sendCommand(command)
    }
    
    func sendActionCommand(action: RobotAction) {
        let command = CommandBuilder.buildActionCommand(action: action)
        connectionManager.sendCommand(command)
    }
}

