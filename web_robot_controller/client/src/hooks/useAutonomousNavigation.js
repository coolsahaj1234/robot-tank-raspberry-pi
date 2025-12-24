import { useEffect, useRef, useCallback } from 'react'

/**
 * Autonomous Navigation Hook - DELIBERATE Control
 * Executes AI navigation commands using chunked, deliberate movements.
 * Robot requires: 70% power for turns, 55%+ for forward movement.
 */
export function useAutonomousNavigation({
  enabled,
  navigationCommand,
  onSendCommand
}) {
  const lastActionRef = useRef(null)
  const commandIntervalRef = useRef(null)

  // Motor power configuration - STRONG turns, CAREFUL movement
  const MOTOR_CONFIG = {
    FORWARD_SPEED: 45,      // Slower forward (safety)
    SLOW_FORWARD: 35,       // Very slow forward
    TURN_SPEED: 90,         // STRONG turn (90% power!)
    BACKUP_SPEED: 50,       // Backup speed
    SCALE_FACTOR: 20        // Scale % to motor values
  }

  const executeMotorCommand = useCallback((leftSpeed, rightSpeed) => {
    const leftMotorValue = Math.round(leftSpeed * MOTOR_CONFIG.SCALE_FACTOR)
    const rightMotorValue = Math.round(rightSpeed * MOTOR_CONFIG.SCALE_FACTOR)
    onSendCommand(`CMD_MOTOR#${leftMotorValue}#${rightMotorValue}`)
  }, [onSendCommand])

  const setLEDs = useCallback((action, dangerZone) => {
    // LED format: CMD_LED#mode#r#g#b#index
    // Mode 1 = static, Mode 4 = breathing

    if (action === 'backup') {
      // RED FLASH for backup - warning!
      onSendCommand('CMD_LED#1#255#0#0#0')
      onSendCommand('CMD_LED#1#255#0#0#1')
      onSendCommand('CMD_LED#1#255#0#0#2')
      onSendCommand('CMD_LED#1#255#0#0#3')
    } else if (dangerZone === 'danger') {
      // Orange warning for danger
      onSendCommand('CMD_LED#1#255#100#0#0')
      onSendCommand('CMD_LED#1#255#100#0#1')
      onSendCommand('CMD_LED#1#255#100#0#2')
      onSendCommand('CMD_LED#1#255#100#0#3')
    } else if (action === 'analyzing') {
      // Blue pulsing while analyzing
      onSendCommand('CMD_LED#4#0#100#255#0')
      onSendCommand('CMD_LED#4#0#100#255#1')
      onSendCommand('CMD_LED#4#0#100#255#2')
      onSendCommand('CMD_LED#4#0#100#255#3')
    } else if (action === 'turn_left') {
      // Amber left side
      onSendCommand('CMD_LED#1#255#200#0#0')
      onSendCommand('CMD_LED#1#255#200#0#1')
      onSendCommand('CMD_LED#1#0#50#50#2')
      onSendCommand('CMD_LED#1#0#50#50#3')
    } else if (action === 'turn_right') {
      // Amber right side
      onSendCommand('CMD_LED#1#0#50#50#0')
      onSendCommand('CMD_LED#1#0#50#50#1')
      onSendCommand('CMD_LED#1#255#200#0#2')
      onSendCommand('CMD_LED#1#255#200#0#3')
    } else if (action === 'forward' || action === 'slow_forward') {
      // Green for forward (dimmer for slow)
      const brightness = action === 'slow_forward' ? 150 : 255
      onSendCommand(`CMD_LED#1#0#${brightness}#100#0`)
      onSendCommand(`CMD_LED#1#0#${brightness}#100#1`)
      onSendCommand(`CMD_LED#1#0#${brightness}#100#2`)
      onSendCommand(`CMD_LED#1#0#${brightness}#100#3`)
    } else {
      // Dim cyan for stopped/idle
      onSendCommand('CMD_LED#1#0#100#100#0')
      onSendCommand('CMD_LED#1#0#100#100#1')
      onSendCommand('CMD_LED#1#0#100#100#2')
      onSendCommand('CMD_LED#1#0#100#100#3')
    }
  }, [onSendCommand])

  useEffect(() => {
    if (!enabled || !navigationCommand) {
      if (commandIntervalRef.current) {
        clearInterval(commandIntervalRef.current)
        commandIntervalRef.current = null
      }
      if (enabled === false) {
        onSendCommand('CMD_MOTOR#0#0')
        // Turn off all LEDs
        onSendCommand('CMD_LED#0#0#0#0#0')
        onSendCommand('CMD_LED#0#0#0#0#1')
        onSendCommand('CMD_LED#0#0#0#0#2')
        onSendCommand('CMD_LED#0#0#0#0#3')
      }
      return
    }

    // Get action from command
    const action = navigationCommand.action || 'stop'
    const dangerZone = navigationCommand.danger_zone || 'clear'
    const state = navigationCommand.state || 'analyzing'
    const distance = navigationCommand.distance || 100

    // Track action for logging (but always execute commands)
    const actionKey = `${action}-${state}`
    const actionChanged = actionKey !== lastActionRef.current
    lastActionRef.current = actionKey

    const executeCommand = () => {
      let leftSpeed = 0
      let rightSpeed = 0

      switch (action) {
        case 'forward':
          // Move forward at normal speed
          leftSpeed = MOTOR_CONFIG.FORWARD_SPEED
          rightSpeed = MOTOR_CONFIG.FORWARD_SPEED
          break

        case 'slow_forward':
          // Move forward slowly (caution)
          leftSpeed = MOTOR_CONFIG.SLOW_FORWARD
          rightSpeed = MOTOR_CONFIG.SLOW_FORWARD
          break

        case 'backup':
          // REVERSE both motors
          leftSpeed = -MOTOR_CONFIG.BACKUP_SPEED
          rightSpeed = -MOTOR_CONFIG.BACKUP_SPEED
          break

        case 'turn_left':
          // Strong left turn - pivot turn
          // Left wheel reverse, right wheel forward
          leftSpeed = -MOTOR_CONFIG.TURN_SPEED * 0.5
          rightSpeed = MOTOR_CONFIG.TURN_SPEED
          break

        case 'turn_right':
          // Strong right turn - pivot turn
          leftSpeed = MOTOR_CONFIG.TURN_SPEED
          rightSpeed = -MOTOR_CONFIG.TURN_SPEED * 0.5
          break

        case 'stop':
        case 'analyzing':
        default:
          // STOP - no movement
          leftSpeed = 0
          rightSpeed = 0
          break
      }

      // Execute motor command
      executeMotorCommand(leftSpeed, rightSpeed)

      // Update LEDs
      setLEDs(action, dangerZone)
    }

    // Log when action changes
    if (actionChanged) {
      console.log(`🤖 AI: Action=${action} State=${state} Distance=${distance}cm Zone=${dangerZone}`)
    }

    executeCommand()

    // Clear any existing interval
    if (commandIntervalRef.current) {
      clearInterval(commandIntervalRef.current)
    }

    // Send commands continuously at 100ms interval
    commandIntervalRef.current = setInterval(executeCommand, 100)

    return () => {
      if (commandIntervalRef.current) {
        clearInterval(commandIntervalRef.current)
        commandIntervalRef.current = null
      }
    }
  }, [enabled, navigationCommand, onSendCommand, executeMotorCommand, setLEDs])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (commandIntervalRef.current) {
        clearInterval(commandIntervalRef.current)
      }
    }
  }, [])
}
