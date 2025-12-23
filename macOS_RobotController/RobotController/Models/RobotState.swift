//
//  RobotState.swift
//  RobotController
//
//  Robot state model
//

import Foundation
import SwiftUI

class RobotState: ObservableObject {
    @Published var isConnected = false
    @Published var currentMode: RobotMode = .stop
    @Published var leftMotorSpeed: Int = 0
    @Published var rightMotorSpeed: Int = 0
    @Published var servo1Angle: Int = 90  // Lift arm
    @Published var servo2Angle: Int = 140 // Claw
    @Published var ultrasonicDistance: Double = 0.0
    @Published var speedLimit: Int = 100
    @Published var ledMode: LEDMode = .breathing
    @Published var ledColor: Color = .green
    @Published var ledR: Int = 0
    @Published var ledG: Int = 255
    @Published var ledB: Int = 0
}

