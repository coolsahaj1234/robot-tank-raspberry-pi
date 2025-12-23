//
//  CommandBuilder.swift
//  RobotController
//
//  Command string formatting utilities
//

import Foundation

struct CommandBuilder {
    static let intervalChar = "#"
    static let endChar = "\n"
    
    static func buildMotorCommand(leftSpeed: Int, rightSpeed: Int) -> String {
        return "\(RobotCommand.motor.rawValue)\(intervalChar)\(leftSpeed)\(intervalChar)\(rightSpeed)\(endChar)"
    }
    
    static func buildServoCommand(index: Int, angle: Int) -> String {
        return "\(RobotCommand.servo.rawValue)\(intervalChar)\(index)\(intervalChar)\(angle)\(endChar)"
    }
    
    static func buildLEDCommand(mode: LEDMode, r: Int, g: Int, b: Int, index: Int = 15) -> String {
        return "\(RobotCommand.led.rawValue)\(intervalChar)\(mode.rawValue)\(intervalChar)\(r)\(intervalChar)\(g)\(intervalChar)\(b)\(intervalChar)\(index)\(endChar)"
    }
    
    static func buildModeCommand(mode: RobotMode) -> String {
        return "\(RobotCommand.mode.rawValue)\(intervalChar)\(mode.rawValue)\(endChar)"
    }
    
    static func buildActionCommand(action: RobotAction) -> String {
        return "\(RobotCommand.action.rawValue)\(intervalChar)\(action.rawValue)\(endChar)"
    }
    
    static func parseResponse(_ message: String) -> (command: String, parameters: [String])? {
        let trimmed = message.trimmingCharacters(in: .whitespacesAndNewlines)
        let parts = trimmed.components(separatedBy: intervalChar)
        guard !parts.isEmpty else { return nil }
        return (parts[0], Array(parts.dropFirst()))
    }
    
    static func parseSonicResponse(_ message: String) -> Double? {
        guard let parsed = parseResponse(message),
              parsed.command == RobotCommand.sonic.rawValue,
              let distance = Double(parsed.parameters.first ?? "") else {
            return nil
        }
        return distance
    }
}

