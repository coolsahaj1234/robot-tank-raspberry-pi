//
//  RobotCommand.swift
//  RobotController
//
//  Command protocol definitions based on old_robot/Server/command.py
//

import Foundation

enum RobotCommand: String {
    case motor = "CMD_MOTOR"
    case led = "CMD_LED"
    case servo = "CMD_SERVO"
    case action = "CMD_ACTION"
    case sonic = "CMD_SONIC"
    case mode = "CMD_MODE"
}

enum RobotMode: Int {
    case stop = 0
    case move = 1
    case sonar = 2
    case infrared = 3
}

enum RobotAction: Int {
    case clampStop = 0
    case clampUp = 1
    case clampDown = 2
}

enum LEDMode: Int {
    case index = 1      // Index control
    case colorWipe = 2  // Color wipe
    case blink = 3      // Blink
    case breathing = 4  // Breathing
    case rainbow = 5    // Rainbow
}

struct MotorCommand {
    let leftSpeed: Int  // -100 to 100
    let rightSpeed: Int // -100 to 100
}

struct ServoCommand {
    let index: Int  // 0 or 1
    let angle: Int  // 0-180
}

struct LEDCommand {
    let mode: LEDMode
    let r: Int      // 0-255
    let g: Int      // 0-255
    let b: Int      // 0-255
    let index: Int  // LED index (typically 15)
}

