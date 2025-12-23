//
//  TCPConnectionManager.swift
//  RobotController
//
//  TCP socket management for command and video streams
//

import Foundation
import Network

protocol TCPConnectionManagerDelegate: AnyObject {
    func didReceiveCommandResponse(_ message: String)
    func didUpdateConnectionStatus(_ isConnected: Bool)
}

class TCPConnectionManager {
    weak var delegate: TCPConnectionManagerDelegate?
    
    private var commandConnection: NWConnection?
    private var videoConnection: NWConnection?
    private let commandQueue = DispatchQueue(label: "com.robotcontroller.command")
    private let videoQueue = DispatchQueue(label: "com.robotcontroller.video")
    
    private var robotIP: String = ""
    private var commandPort: UInt16 = 5003
    private var videoPort: UInt16 = 8003
    
    var isConnected: Bool {
        return commandConnection?.state == .ready && videoConnection?.state == .ready
    }
    
    func connect(ip: String, commandPort: Int, videoPort: Int) {
        self.robotIP = ip
        self.commandPort = UInt16(commandPort)
        self.videoPort = UInt16(videoPort)
        
        connectCommandSocket()
        connectVideoSocket()
    }
    
    func disconnect() {
        commandConnection?.cancel()
        videoConnection?.cancel()
        commandConnection = nil
        videoConnection = nil
        delegate?.didUpdateConnectionStatus(false)
    }
    
    func sendCommand(_ command: String) {
        guard let connection = commandConnection,
              connection.state == .ready else {
            print("Command socket not ready")
            return
        }
        
        guard let data = command.data(using: .utf8) else {
            print("Failed to encode command")
            return
        }
        
        connection.send(content: data, completion: .contentProcessed { error in
            if let error = error {
                print("Error sending command: \(error)")
            }
        })
    }
    
    private func connectCommandSocket() {
        let host = NWEndpoint.Host(robotIP)
        let port = NWEndpoint.Port(integerLiteral: commandPort)
        let parameters = NWParameters.tcp
        
        commandConnection = NWConnection(host: host, port: port, using: parameters)
        commandConnection?.stateUpdateHandler = { [weak self] state in
            DispatchQueue.main.async {
                switch state {
                case .ready:
                    print("Command socket connected")
                    self?.receiveCommandData()
                    if self?.videoConnection?.state == .ready {
                        self?.delegate?.didUpdateConnectionStatus(true)
                    }
                case .failed(let error):
                    print("Command socket failed: \(error)")
                    self?.delegate?.didUpdateConnectionStatus(false)
                case .waiting(let error):
                    print("Command socket waiting: \(error)")
                case .cancelled:
                    print("Command socket cancelled")
                    self?.delegate?.didUpdateConnectionStatus(false)
                default:
                    break
                }
            }
        }
        
        commandConnection?.start(queue: commandQueue)
    }
    
    private func connectVideoSocket() {
        let host = NWEndpoint.Host(robotIP)
        let port = NWEndpoint.Port(integerLiteral: videoPort)
        let parameters = NWParameters.tcp
        
        videoConnection = NWConnection(host: host, port: port, using: parameters)
        videoConnection?.stateUpdateHandler = { [weak self] state in
            DispatchQueue.main.async {
                switch state {
                case .ready:
                    print("Video socket connected")
                    if self?.commandConnection?.state == .ready {
                        self?.delegate?.didUpdateConnectionStatus(true)
                    }
                case .failed(let error):
                    print("Video socket failed: \(error)")
                    self?.delegate?.didUpdateConnectionStatus(false)
                case .waiting(let error):
                    print("Video socket waiting: \(error)")
                case .cancelled:
                    print("Video socket cancelled")
                    self?.delegate?.didUpdateConnectionStatus(false)
                default:
                    break
                }
            }
        }
        
        videoConnection?.start(queue: videoQueue)
    }
    
    private func receiveCommandData() {
        commandConnection?.receive(minimumIncompleteLength: 1, maximumLength: 1024) { [weak self] data, _, isComplete, error in
            if let error = error {
                print("Error receiving command data: \(error)")
                return
            }
            
            if let data = data, !data.isEmpty {
                if let message = String(data: data, encoding: .utf8) {
                    DispatchQueue.main.async {
                        self?.delegate?.didReceiveCommandResponse(message)
                    }
                }
            }
            
            if !isComplete {
                self?.receiveCommandData()
            }
        }
    }
    
    func receiveVideoData(completion: @escaping (Data?) -> Void) {
        guard let connection = videoConnection,
              connection.state == .ready else {
            DispatchQueue.main.async {
                completion(nil)
            }
            return
        }
        
        // First, receive the 4-byte length header
        connection.receive(minimumIncompleteLength: 4, maximumLength: 4) { [weak self] lengthData, _, isComplete, error in
            if let error = error {
                print("Error receiving video length: \(error)")
                DispatchQueue.main.async {
                    completion(nil)
                }
                return
            }
            
            guard let lengthData = lengthData, lengthData.count == 4 else {
                DispatchQueue.main.async {
                    completion(nil)
                }
                return
            }
            
            // Parse little-endian UInt32
            let length = lengthData.withUnsafeBytes { bytes in
                UInt32(bytes[0]) | (UInt32(bytes[1]) << 8) | (UInt32(bytes[2]) << 16) | (UInt32(bytes[3]) << 24)
            }
            let frameLength = Int(length)
            
            if frameLength > 0 && frameLength < 10_000_000 { // Sanity check
                // Now receive the actual frame data
                connection.receive(minimumIncompleteLength: frameLength, maximumLength: frameLength) { [weak self] frameData, _, _, error in
                    if let error = error {
                        print("Error receiving video frame: \(error)")
                        DispatchQueue.main.async {
                            completion(nil)
                        }
                        return
                    }
                    
                    DispatchQueue.main.async {
                        completion(frameData)
                    }
                    
                    // Continue receiving next frame header
                    if !isComplete {
                        self?.receiveVideoData(completion: completion)
                    }
                }
            } else {
                DispatchQueue.main.async {
                    completion(nil)
                }
                // Continue receiving next frame header
                if !isComplete {
                    self?.receiveVideoData(completion: completion)
                }
            }
        }
    }
}

