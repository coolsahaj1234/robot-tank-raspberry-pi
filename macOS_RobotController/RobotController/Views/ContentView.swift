//
//  ContentView.swift
//  RobotController
//
//  Main container view
//

import SwiftUI

struct ContentView: View {
    @StateObject private var viewModel = RobotViewModel()
    @State private var showSettings = false
    
    var body: some View {
        ZStack {
            DashboardView(viewModel: viewModel)
            
            // Sidebar Navigation
            VStack {
                HStack {
                    // Connection Status Indicator
                    Button(action: {
                        if viewModel.robotState.isConnected {
                            viewModel.disconnect()
                        } else {
                            viewModel.connect()
                        }
                    }) {
                        Image(systemName: viewModel.robotState.isConnected ? "wifi" : "wifi.slash")
                            .font(.system(size: 20))
                            .foregroundColor(viewModel.robotState.isConnected ? Color(red: 0, green: 1, blue: 0.53) : .red)
                            .frame(width: 44, height: 44)
                            .background(Color(red: 0.2, green: 0.2, blue: 0.2))
                            .cornerRadius(8)
                    }
                    .buttonStyle(PlainButtonStyle())
                    .padding(.leading, 16)
                    .padding(.top, 16)
                    
                    Spacer()
                }
                
                Spacer()
                
                // Settings Button
                HStack {
                    Button(action: {
                        showSettings = true
                    }) {
                        Image(systemName: "gearshape")
                            .font(.system(size: 20))
                            .foregroundColor(.gray)
                            .frame(width: 44, height: 44)
                            .background(Color(red: 0.2, green: 0.2, blue: 0.2))
                            .cornerRadius(8)
                    }
                    .buttonStyle(PlainButtonStyle())
                    .padding(.leading, 16)
                    .padding(.bottom, 16)
                    
                    Spacer()
                }
            }
        }
        .sheet(isPresented: $showSettings) {
            SettingsView(viewModel: viewModel)
        }
    }
}

