//
//  VideoView.swift
//  RobotController
//
//  Video feed display view
//

import SwiftUI
import AppKit

struct VideoView: View {
    let image: NSImage?
    
    var body: some View {
        ZStack {
            Color.black
            
            if let image = image {
                Image(nsImage: image)
                    .resizable()
                    .aspectRatio(contentMode: .fit)
            } else {
                VStack {
                    Image(systemName: "video.slash")
                        .font(.system(size: 48))
                        .foregroundColor(.gray)
                    Text("No Video Feed")
                        .foregroundColor(.gray)
                        .padding(.top, 8)
                }
            }
            
            VStack {
                HStack {
                    Text("FRONT CAMERA")
                        .font(.system(size: 10, design: .monospaced))
                        .foregroundColor(.green)
                        .padding(8)
                        .background(Color.black.opacity(0.5))
                        .cornerRadius(8)
                    Spacer()
                }
                .padding()
                Spacer()
            }
        }
        .cornerRadius(16)
    }
}

