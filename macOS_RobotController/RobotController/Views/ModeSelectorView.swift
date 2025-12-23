//
//  ModeSelectorView.swift
//  RobotController
//
//  Mode selection view
//

import SwiftUI

struct ModeSelectorView: View {
    @ObservedObject var viewModel: RobotViewModel
    @Binding var selectedMode: RobotMode
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("AUTONOMY LEVEL")
                .font(.system(size: 10, weight: .bold))
                .foregroundColor(.gray)
                .tracking(1)
            
            HStack(spacing: 4) {
                ModeButton(mode: .stop, title: "STOP", selectedMode: $selectedMode) {
                    viewModel.setMode(.stop)
                }
                ModeButton(mode: .move, title: "MOVE", selectedMode: $selectedMode) {
                    viewModel.setMode(.move)
                }
                ModeButton(mode: .sonar, title: "SONAR", selectedMode: $selectedMode) {
                    viewModel.setMode(.sonar)
                }
                ModeButton(mode: .infrared, title: "INFRARED", selectedMode: $selectedMode) {
                    viewModel.setMode(.infrared)
                }
            }
            .padding(4)
            .background(Color(red: 0.15, green: 0.15, blue: 0.15))
            .cornerRadius(8)
        }
    }
}

struct ModeButton: View {
    let mode: RobotMode
    let title: String
    @Binding var selectedMode: RobotMode
    let action: () -> Void
    
    var isSelected: Bool {
        selectedMode == mode
    }
    
    var body: some View {
        Button(action: {
            selectedMode = mode
            action()
        }) {
            Text(title)
                .font(.system(size: 11, weight: .medium))
                .frame(maxWidth: .infinity)
                .padding(.vertical, 8)
                .background(isSelected ? Color(red: 0, green: 1, blue: 0.53) : Color.clear)
                .foregroundColor(isSelected ? .black : .gray)
                .cornerRadius(6)
        }
        .buttonStyle(PlainButtonStyle())
    }
}

