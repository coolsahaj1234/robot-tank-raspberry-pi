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
<<<<<<< HEAD
=======
  const wasEnabledRef = useRef(false)
>>>>>>> 40885bf (Initial commit)

  // Motor power configuration - STRONG turns, CAREFUL movement
  const MOTOR_CONFIG = {
    FORWARD_SPEED: 45,      // Slower forward (safety)
    SLOW_FORWARD: 35,       // Very slow forward
    TURN_SPEED: 90,         // STRONG turn (90% power!)
<<<<<<< HEAD
    BACKUP_SPEED: 50,       // Backup speed
    SCALE_FACTOR: 20        // Scale % to motor values
=======
    GENTLE_TURN_SPEED: 50,  // Gentle turn for tracking (50% power)
    BACKUP_SPEED: 50,       // Backup speed
    SCALE_FACTOR: 20,       // Scale % to motor values
    MOTOR_COMPENSATION: 0.97 // Left motor runs at 97% of right motor (compensate for imbalance)
>>>>>>> 40885bf (Initial commit)
  }

  const executeMotorCommand = useCallback((leftSpeed, rightSpeed) => {
    const leftMotorValue = Math.round(leftSpeed * MOTOR_CONFIG.SCALE_FACTOR)
    const rightMotorValue = Math.round(rightSpeed * MOTOR_CONFIG.SCALE_FACTOR)
    onSendCommand(`CMD_MOTOR#${leftMotorValue}#${rightMotorValue}`)
  }, [onSendCommand])

  const setLEDs = useCallback((action, dangerZone) => {
    // LED format: CMD_LED#mode#r#g#b#index
<<<<<<< HEAD
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
=======
    if (action === 'backup') {
      for (let i = 0; i < 4; i++) onSendCommand(`CMD_LED#1#255#0#0#${i}`)
    } else if (dangerZone === 'danger') {
      for (let i = 0; i < 4; i++) onSendCommand(`CMD_LED#1#255#100#0#${i}`)
    } else if (action === 'analyzing') {
      for (let i = 0; i < 4; i++) onSendCommand(`CMD_LED#4#0#100#255#${i}`)
    } else if (action === 'turn_left' || action === 'scanning_left' || action === 'gentle_turn_left') {
      // Left indicator - Green Blink (mode 3)
      onSendCommand('CMD_LED#3#0#255#0#0')
      onSendCommand('CMD_LED#3#0#255#0#1')
      // Right side - TURN OFF
      onSendCommand('CMD_LED#0#0#0#0#2')
      onSendCommand('CMD_LED#0#0#0#0#3')
    } else if (action === 'turn_right' || action === 'scanning_right' || action === 'gentle_turn_right') {
      // Left side - TURN OFF
      onSendCommand('CMD_LED#0#0#0#0#0')
      onSendCommand('CMD_LED#0#0#0#0#1')
      // Right indicator - Green Blink (mode 3)
      onSendCommand('CMD_LED#3#0#255#0#2')
      onSendCommand('CMD_LED#3#0#255#0#3')
    } else if (action === 'forward' || action === 'slow_forward') {
      const b = action === 'slow_forward' ? 150 : 255
      for (let i = 0; i < 4; i++) onSendCommand(`CMD_LED#1#0#${b}#100#${i}`)
    } else if (action === 'santa_spotted') {
      // Purple pulse for Santa detection (mode 4 = pulse)
      for (let i = 0; i < 4; i++) onSendCommand(`CMD_LED#4#200#0#255#${i}`)
    } else {
      for (let i = 0; i < 4; i++) onSendCommand(`CMD_LED#1#0#100#100#${i}`)
>>>>>>> 40885bf (Initial commit)
    }
  }, [onSendCommand])

  useEffect(() => {
<<<<<<< HEAD
    if (!enabled || !navigationCommand) {
=======
    if (!enabled) {
      // CRITICAL: Clear interval IMMEDIATELY
>>>>>>> 40885bf (Initial commit)
      if (commandIntervalRef.current) {
        clearInterval(commandIntervalRef.current)
        commandIntervalRef.current = null
      }
<<<<<<< HEAD
      if (enabled === false) {
        onSendCommand('CMD_MOTOR#0#0')
        // Turn off all LEDs
        onSendCommand('CMD_LED#0#0#0#0#0')
        onSendCommand('CMD_LED#0#0#0#0#1')
        onSendCommand('CMD_LED#0#0#0#0#2')
        onSendCommand('CMD_LED#0#0#0#0#3')
=======

      // CRITICAL: Send MULTIPLE stop commands for redundancy
      if (wasEnabledRef.current) {
        console.log('🛑 AI: EMERGENCY STOP - Autonomous mode disabled')

        // Send stop command 3 times for reliability
        onSendCommand('CMD_MOTOR#0#0')
        onSendCommand('CMD_MOTOR#0#0')
        onSendCommand('CMD_MOTOR#0#0')

        // Turn off all LEDs
        for (let i = 0; i < 4; i++) onSendCommand(`CMD_LED#0#0#0#0#${i}`)

        wasEnabledRef.current = false
>>>>>>> 40885bf (Initial commit)
      }
      return
    }

<<<<<<< HEAD
=======
    if (!navigationCommand) return

    // We are now enabled and have a command
    wasEnabledRef.current = true

>>>>>>> 40885bf (Initial commit)
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

<<<<<<< HEAD
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
=======
      // Use dynamic speed from AI if provided, otherwise fallback to defaults
      const requestedSpeed = navigationCommand.speed || 0
      const turnSpeed = navigationCommand.speed || MOTOR_CONFIG.TURN_SPEED
      const forwardSpeed = navigationCommand.speed || MOTOR_CONFIG.FORWARD_SPEED
      const backupSpeed = navigationCommand.speed || MOTOR_CONFIG.BACKUP_SPEED

      switch (action) {
        case 'forward':
          // Move forward at requested speed with motor compensation
          leftSpeed = forwardSpeed * MOTOR_CONFIG.MOTOR_COMPENSATION
          rightSpeed = forwardSpeed
          break

        case 'slow_forward':
          // Move forward slowly with motor compensation
          leftSpeed = (requestedSpeed || MOTOR_CONFIG.SLOW_FORWARD) * MOTOR_CONFIG.MOTOR_COMPENSATION
          rightSpeed = requestedSpeed || MOTOR_CONFIG.SLOW_FORWARD
>>>>>>> 40885bf (Initial commit)
          break

        case 'backup':
          // REVERSE both motors
<<<<<<< HEAD
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
=======
          leftSpeed = -backupSpeed
          rightSpeed = -backupSpeed
          break

        case 'turn_left':
          // Strong left turn - BOTH motors at equal power, opposite directions
          // Left wheel reverse, right wheel forward at SAME power for pivot
          leftSpeed = -turnSpeed
          rightSpeed = turnSpeed
          break

        case 'turn_right':
          // Strong right turn - BOTH motors at equal power, opposite directions
          // Right wheel reverse, left wheel forward at SAME power for pivot
          leftSpeed = turnSpeed
          rightSpeed = -turnSpeed
          break

        case 'gentle_turn_left':
          // Gentle left turn for tracking - BOTH motors at equal power
          const gentleTurnSpeed = requestedSpeed || MOTOR_CONFIG.GENTLE_TURN_SPEED
          leftSpeed = -gentleTurnSpeed
          rightSpeed = gentleTurnSpeed
          break

        case 'gentle_turn_right':
          // Gentle right turn for tracking - BOTH motors at equal power
          const gentleTurnSpeedR = requestedSpeed || MOTOR_CONFIG.GENTLE_TURN_SPEED
          leftSpeed = gentleTurnSpeedR
          rightSpeed = -gentleTurnSpeedR
          break

        case 'pickup':
          // EXCLUSIVE PICKUP ACTION - STRICT VALIDATION
          // Stop motors first
          leftSpeed = 0
          rightSpeed = 0

          // CRITICAL: Only trigger pickup if explicitly in pickup state
          // AND action changed (prevent spam)
          if (actionChanged && action === 'pickup') {
            console.log('🎅 AI: SANTA HAT PICKUP INITIATED!')
            onSendCommand('CMD_ACTION#1')
          }
          break

        case 'stop':
        case 'stopped':
>>>>>>> 40885bf (Initial commit)
        case 'analyzing':
        default:
          // STOP - no movement
          leftSpeed = 0
          rightSpeed = 0
          break
      }

<<<<<<< HEAD
=======
      // CRITICAL SAFETY: Execute stop commands FIRST before any motor commands
      if (action === 'stop' || action === 'stopped' || action === 'analyzing') {
        onSendCommand('CMD_MOTOR#0#0')
        leftSpeed = 0
        rightSpeed = 0
      }

>>>>>>> 40885bf (Initial commit)
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

<<<<<<< HEAD
    // Send commands continuously at 100ms interval
    commandIntervalRef.current = setInterval(executeCommand, 100)
=======
    // Send commands continuously at 50ms interval for responsive control
    commandIntervalRef.current = setInterval(executeCommand, 50)
>>>>>>> 40885bf (Initial commit)

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
