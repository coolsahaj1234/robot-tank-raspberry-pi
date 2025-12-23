//
//  LEDControlView.swift
//  RobotController
//
//  LED control view with color picker and mode selector
//

import SwiftUI

struct LEDControlView: View {
    @ObservedObject var viewModel: RobotViewModel
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("LED CONTROL")
                    .font(.system(size: 10, design: .monospaced))
                    .foregroundColor(.gray)
                Spacer()
                ColorPicker("", selection: Binding(
                    get: { viewModel.robotState.ledColor },
                    set: { color in
                        viewModel.setLED(mode: viewModel.robotState.ledMode, color: color)
                    }
                ))
                .labelsHidden()
            }
            
            Picker("Mode", selection: Binding(
                get: { viewModel.robotState.ledMode },
                set: { mode in
                    viewModel.setLED(mode: mode, color: viewModel.robotState.ledColor)
                }
            )) {
                Text("Index Control").tag(LEDMode.index)
                Text("Color Wipe").tag(LEDMode.colorWipe)
                Text("Blink").tag(LEDMode.blink)
                Text("Breathing").tag(LEDMode.breathing)
                Text("Rainbow").tag(LEDMode.rainbow)
            }
            .pickerStyle(.menu)
            .frame(maxWidth: .infinity)
            .padding(8)
            .background(Color(red: 0.2, green: 0.2, blue: 0.2))
            .cornerRadius(8)
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

