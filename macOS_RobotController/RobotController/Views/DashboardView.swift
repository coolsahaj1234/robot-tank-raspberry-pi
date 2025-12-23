//
//  DashboardView.swift
//  RobotController
//
//  Main dashboard view with video and controls
//

import SwiftUI

struct DashboardView: View {
    @ObservedObject var viewModel: RobotViewModel
    
    var body: some View {
        HStack(spacing: 16) {
            // Left Panel - Video Feed
            VStack(spacing: 16) {
                VideoView(image: viewModel.currentVideoFrame)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                
                SensorDataView(viewModel: viewModel)
            }
            .frame(maxWidth: .infinity)
            
            // Right Panel - Controls
            ScrollView {
                VStack(spacing: 16) {
                    // Connection Status
                    HStack {
                        Circle()
                            .fill(viewModel.robotState.isConnected ? Color.green : Color.red)
                            .frame(width: 8, height: 8)
                        Text(viewModel.robotState.isConnected ? "Connected" : "Disconnected")
                            .font(.system(size: 12))
                            .foregroundColor(.gray)
                        Spacer()
                    }
                    .padding(.horizontal)
                    
                    // Mode Selector
                    ModeSelectorView(viewModel: viewModel, selectedMode: $viewModel.robotState.currentMode)
                        .padding(.horizontal)
                    
                    // Control Panel
                    ControlPanelView(viewModel: viewModel)
                        .padding(.horizontal)
                    
                    // LED Control
                    LEDControlView(viewModel: viewModel)
                        .padding(.horizontal)
                    
                    // Quick Actions
                    VStack(alignment: .leading, spacing: 12) {
                        Text("QUICK ACTIONS")
                            .font(.system(size: 10, weight: .bold))
                            .foregroundColor(.gray)
                            .tracking(1)
                        
                        HStack(spacing: 8) {
                            ActionButton(title: "Clamp Up", icon: "arrow.up", action: {
                                viewModel.performAction(.clampUp)
                            })
                            ActionButton(title: "Clamp Down", icon: "arrow.down", action: {
                                viewModel.performAction(.clampDown)
                            })
                            ActionButton(title: "Clamp Stop", icon: "stop.fill", action: {
                                viewModel.performAction(.clampStop)
                            })
                        }
                    }
                    .padding(.horizontal)
                    
                    Spacer()
                }
                .padding(.vertical)
            }
            .frame(width: 400)
            .background(Color(red: 0.16, green: 0.16, blue: 0.16))
        }
        .padding()
        .background(Color(red: 0.1, green: 0.1, blue: 0.1))
    }
}

struct ActionButton: View {
    let title: String
    let icon: String
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            VStack(spacing: 4) {
                Image(systemName: icon)
                    .font(.system(size: 18))
                Text(title)
                    .font(.system(size: 11))
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 12)
            .background(Color(red: 0.2, green: 0.2, blue: 0.2))
            .foregroundColor(.white)
            .cornerRadius(8)
        }
        .buttonStyle(PlainButtonStyle())
        .onHover { hovering in
            // Add hover effect if needed
        }
    }
}

