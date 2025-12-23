//
//  VideoStreamService.swift
//  RobotController
//
//  Video frame receiving and decoding service
//

import Foundation
import AppKit
import CoreImage

protocol VideoStreamServiceDelegate: AnyObject {
    func didReceiveVideoFrame(_ image: NSImage)
}

class VideoStreamService {
    weak var delegate: VideoStreamServiceDelegate?
    private let connectionManager: TCPConnectionManager
    private var isReceiving = false
    
    init(connectionManager: TCPConnectionManager) {
        self.connectionManager = connectionManager
    }
    
    func startReceiving() {
        guard !isReceiving else { return }
        isReceiving = true
        receiveNextFrame()
    }
    
    func stopReceiving() {
        isReceiving = false
    }
    
    private func receiveNextFrame() {
        guard isReceiving else { return }
        
        connectionManager.receiveVideoData { [weak self] frameData in
            guard let self = self else { return }
            
            if let frameData = frameData {
                self.processFrame(frameData)
            }
            
            // Continue receiving next frame
            DispatchQueue.global(qos: .userInitiated).async {
                if self.isReceiving {
                    self.receiveNextFrame()
                }
            }
        }
    }
    
    private func processFrame(_ data: Data) {
        guard let image = NSImage(data: data) else {
            print("Failed to create image from frame data")
            return
        }
        
        DispatchQueue.main.async { [weak self] in
            self?.delegate?.didReceiveVideoFrame(image)
        }
    }
}

