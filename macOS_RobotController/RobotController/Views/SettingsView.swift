//
//  SettingsView.swift
//  RobotController
//
//  Settings view for connection configuration
//

import SwiftUI

struct SettingsView: View {
    @ObservedObject var viewModel: RobotViewModel
    @Environment(\.dismiss) var dismiss
    
    var body: some View {
        VStack(spacing: 20) {
            Text("Connection Settings")
                .font(.system(size: 18, weight: .bold))
                .padding(.top)
            
            Form {
                TextField("Robot IP Address", text: $viewModel.connectionSettings.robotIP)
                    .textFieldStyle(.roundedBorder)
                
                HStack {
                    Text("Command Port:")
                    TextField("", value: $viewModel.connectionSettings.commandPort, format: .number)
                        .textFieldStyle(.roundedBorder)
                        .frame(width: 100)
                }
                
                HStack {
                    Text("Video Port:")
                    TextField("", value: $viewModel.connectionSettings.videoPort, format: .number)
                        .textFieldStyle(.roundedBorder)
                        .frame(width: 100)
                }
                
                Toggle("Auto Reconnect", isOn: $viewModel.connectionSettings.autoReconnect)
            }
            .padding()
            
            HStack(spacing: 12) {
                Button("Cancel") {
                    dismiss()
                }
                .keyboardShortcut(.cancelAction)
                
                Button("Save") {
                    dismiss()
                }
                .keyboardShortcut(.defaultAction)
                .buttonStyle(.borderedProminent)
            }
            .padding(.bottom)
        }
        .frame(width: 400, height: 300)
    }
}

