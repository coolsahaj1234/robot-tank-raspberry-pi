//
//  ControlPanelView.swift
//  RobotController
//
//  Motor and servo control panel
//

import SwiftUI

struct ControlPanelView: View {
    @ObservedObject var viewModel: RobotViewModel
    
    var body: some View {
        VStack(spacing: 20) {
            // Directional Pad
            DirectionalPadView(viewModel: viewModel)
            
            // Speed Control
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text("SPEED LIMIT")
                        .font(.system(size: 10))
                        .foregroundColor(.gray)
                    Spacer()
                    Text("\(viewModel.robotState.speedLimit)%")
                        .font(.system(size: 10))
                        .foregroundColor(.gray)
                }
                Slider(value: Binding(
                    get: { Double(viewModel.robotState.speedLimit) },
                    set: { viewModel.robotState.speedLimit = Int($0) }
                ), in: 0...100)
                .tint(Color(red: 0, green: 1, blue: 0.53))
            }
            .padding(.horizontal, 16)
            
            Divider()
                .background(Color.gray.opacity(0.3))
            
            // Servo Controls
            VStack(alignment: .leading, spacing: 16) {
                Text("ROBOT ARM")
                    .font(.system(size: 10, design: .monospaced))
                    .foregroundColor(.gray)
                    .padding(.bottom, 4)
                
                // Servo 1 - Lift
                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Text("LIFT HEIGHT")
                            .font(.system(size: 10))
                            .foregroundColor(.gray)
                        Spacer()
                        Text("\(viewModel.robotState.servo1Angle)°")
                            .font(.system(size: 10))
                            .foregroundColor(.gray)
                    }
                    Slider(value: Binding(
                        get: { Double(viewModel.robotState.servo1Angle) },
                        set: { viewModel.setServo1Angle(Int($0)) }
                    ), in: 0...180)
                    .tint(.blue)
                }
                
                // Servo 2 - Claw
                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Text("CLAW GRIP")
                            .font(.system(size: 10))
                            .foregroundColor(.gray)
                        Spacer()
                        Text("\(viewModel.robotState.servo2Angle)°")
                            .font(.system(size: 10))
                            .foregroundColor(.gray)
                    }
                    Slider(value: Binding(
                        get: { Double(viewModel.robotState.servo2Angle) },
                        set: { viewModel.setServo2Angle(Int($0)) }
                    ), in: 0...180)
                    .tint(.purple)
                }
            }
        }
        .padding()
        .background(Color(red: 0.15, green: 0.15, blue: 0.15).opacity(0.5))
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(Color.gray.opacity(0.3), style: StrokeStyle(lineWidth: 1, dash: [5]))
        )
    }
}

struct DirectionalPadView: View {
    @ObservedObject var viewModel: RobotViewModel
    
    var body: some View {
        VStack(spacing: 8) {
            Text("DIRECTION CONTROL")
                .font(.system(size: 10, design: .monospaced))
                .foregroundColor(.gray)
            
            // 3x3 Grid
            VStack(spacing: 4) {
                // Top row
                HStack(spacing: 4) {
                    DirectionButton(icon: "arrow.up.left", action: {
                        viewModel.move(x: -1, y: 1)
                    }, onRelease: {
                        viewModel.stopMotors()
                    })
                    DirectionButton(icon: "arrow.up", action: {
                        viewModel.move(x: 0, y: 1)
                    }, onRelease: {
                        viewModel.stopMotors()
                    })
                    DirectionButton(icon: "arrow.up.right", action: {
                        viewModel.move(x: 1, y: 1)
                    }, onRelease: {
                        viewModel.stopMotors()
                    })
                }
                
                // Middle row
                HStack(spacing: 4) {
                    DirectionButton(icon: "arrow.left", action: {
                        viewModel.move(x: -1, y: 0)
                    }, onRelease: {
                        viewModel.stopMotors()
                    })
                    Color.clear.frame(width: 44, height: 44)
                    DirectionButton(icon: "arrow.right", action: {
                        viewModel.move(x: 1, y: 0)
                    }, onRelease: {
                        viewModel.stopMotors()
                    })
                }
                
                // Bottom row
                HStack(spacing: 4) {
                    DirectionButton(icon: "arrow.down.left", action: {
                        viewModel.move(x: -1, y: -1)
                    }, onRelease: {
                        viewModel.stopMotors()
                    })
                    DirectionButton(icon: "arrow.down", action: {
                        viewModel.move(x: 0, y: -1)
                    }, onRelease: {
                        viewModel.stopMotors()
                    })
                    DirectionButton(icon: "arrow.down.right", action: {
                        viewModel.move(x: 1, y: -1)
                    }, onRelease: {
                        viewModel.stopMotors()
                    })
                }
            }
            
            Text("KEYBOARD ARROWS SUPPORTED")
                .font(.system(size: 8, design: .monospaced))
                .foregroundColor(.gray.opacity(0.7))
                .padding(.top, 4)
        }
    }
}

struct DirectionButton: View {
    let icon: String
    let action: () -> Void
    let onRelease: () -> Void
    @State private var isPressed = false
    
    var body: some View {
        ZStack {
            Image(systemName: icon)
                .font(.system(size: 20))
                .foregroundColor(isPressed ? .black : .white)
                .frame(width: 44, height: 44)
                .background(isPressed ? Color(red: 0, green: 1, blue: 0.53) : Color(red: 0.2, green: 0.2, blue: 0.2))
                .cornerRadius(8)
        }
        .gesture(
            DragGesture(minimumDistance: 0)
                .onChanged { _ in
                    if !isPressed {
                        isPressed = true
                        action()
                    }
                }
                .onEnded { _ in
                    isPressed = false
                    onRelease()
                }
        )
    }
}

