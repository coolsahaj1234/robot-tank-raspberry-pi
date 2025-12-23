//
//  SensorDataView.swift
//  RobotController
//
//  Sensor readings display view
//

import SwiftUI

struct SensorDataView: View {
    @ObservedObject var viewModel: RobotViewModel
    
    var body: some View {
        HStack(spacing: 12) {
            // Battery (placeholder - not in old server)
            VStack(alignment: .leading, spacing: 4) {
                Text("Battery")
                    .font(.system(size: 10))
                    .foregroundColor(.gray)
                Text("100%")
                    .font(.system(size: 20, weight: .bold))
                    .foregroundColor(Color(red: 0, green: 1, blue: 0.53))
            }
            .frame(maxWidth: .infinity)
            .padding()
            .background(Color(red: 0.2, green: 0.2, blue: 0.2).opacity(0.5))
            .cornerRadius(12)
            
            // Ultrasonic Distance
            VStack(alignment: .leading, spacing: 4) {
                Text("FRONT SONAR")
                    .font(.system(size: 10))
                    .foregroundColor(.gray)
                Text(String(format: "%.1f cm", viewModel.robotState.ultrasonicDistance))
                    .font(.system(size: 18, weight: .bold))
                    .foregroundColor(.blue)
            }
            .frame(maxWidth: .infinity)
            .padding()
            .background(Color(red: 0.2, green: 0.2, blue: 0.2).opacity(0.5))
            .cornerRadius(12)
            
            // Status
            VStack(alignment: .leading, spacing: 4) {
                Text("Status")
                    .font(.system(size: 10))
                    .foregroundColor(.gray)
                Text(viewModel.robotState.isConnected ? "Online" : "Offline")
                    .font(.system(size: 16, weight: .bold))
                    .foregroundColor(viewModel.robotState.isConnected ? .green : .red)
            }
            .frame(maxWidth: .infinity)
            .padding()
            .background(Color(red: 0.2, green: 0.2, blue: 0.2).opacity(0.5))
            .cornerRadius(12)
        }
    }
}

