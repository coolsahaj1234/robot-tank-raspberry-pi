#!/usr/bin/env node

/**
 * Main startup script for Robot Tank Controller
 * Starts Node.js bridge server, React frontend, and Python AI service
 */

const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

// Colors for terminal output
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m'
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function checkCommand(command) {
  try {
    const cmd = process.platform === 'win32' ? `where ${command}` : `which ${command}`;
    require('child_process').execSync(cmd, { stdio: 'ignore' });
    return true;
  } catch {
    // Fallback for Windows if 'where' fails (sometimes happens with built-ins or aliases)
    try {
      require('child_process').execSync(`${command} --version`, { stdio: 'ignore' });
      return true;
    } catch {
      return false;
    }
  }
}

function checkPort(port) {
  return new Promise((resolve) => {
    const net = require('net');
    const server = net.createServer();
    server.listen(port, '0.0.0.0', () => {
      server.once('close', () => resolve(true));
      server.close();
    });
    server.on('error', () => resolve(false));
  });
}

function killProcessOnPort(port) {
  try {
    if (process.platform === 'win32') {
      try {
        const findCmd = `netstat -aon | findstr :${port} | findstr LISTENING`;
        const output = require('child_process').execSync(findCmd).toString();
        const lines = output.split('\n');
        for (const line of lines) {
          const parts = line.trim().split(/\s+/);
          const pid = parts[parts.length - 1];
          if (pid && !isNaN(pid) && pid > 0) {
            log(`  Cleaning up process ${pid} on port ${port}...`, 'yellow');
            require('child_process').execSync(`taskkill /F /PID ${pid} /T`, { stdio: 'ignore' });
          }
        }
      } catch (e) {
        // Findstr returns exit code 1 if no match found, which is fine
      }
    } else {
      try {
        require('child_process').execSync(`lsof -ti:${port} | xargs kill -9`, { stdio: 'ignore' });
      } catch (e) { }
    }
  } catch (e) {
    log(`  Warning: Could not clean up port ${port}: ${e.message}`, 'yellow');
  }
}

let pythonCmd = 'python3';
let pipCmd = 'pip3';

async function checkPrerequisites() {
  log('\n🤖 Robot Tank Controller - Starting All Services\n', 'blue');
  log('📋 Checking prerequisites...', 'yellow');

  // Check Node.js
  if (!checkCommand('node')) {
    log('❌ Node.js is not installed. Please install Node.js first.', 'red');
    process.exit(1);
  }
  const nodeVersion = require('child_process').execSync('node --version').toString().trim();
  log(`✅ Node.js: ${nodeVersion}`, 'green');

  // Check npm
  if (!checkCommand('npm')) {
    log('❌ npm is not installed. Please install npm first.', 'red');
    process.exit(1);
  }
  const npmVersion = require('child_process').execSync('npm --version').toString().trim();
  log(`✅ npm: ${npmVersion}`, 'green');

  // Check Python 3
  if (!checkCommand('python3')) {
    if (checkCommand('python')) {
      pythonCmd = 'python';
    } else {
      log('❌ Python is not installed. Please install Python first.', 'red');
      process.exit(1);
    }
  }
  const pythonVersion = require('child_process').execSync(`${pythonCmd} --version`).toString().trim();
  log(`✅ ${pythonVersion}`, 'green');

  // Check pip
  if (!checkCommand('pip3')) {
    if (checkCommand('pip')) {
      pipCmd = 'pip';
    } else {
      log('❌ pip is not installed. Please install pip first.', 'red');
      process.exit(1);
    }
  }
  log(`✅ ${pipCmd} installed`, 'green');

  log('');
  log('🔍 Checking ports and cleaning up stale processes...', 'yellow');

  const ports = [3001, 3002, 5001, 5173];

  // Extra aggressive cleanup for Python processes on Windows
  if (process.platform === 'win32') {
    try {
      require('child_process').execSync('taskkill /F /IM python.exe /T', { stdio: 'ignore' });
    } catch (e) { }
  }

  for (const port of ports) {
    const available = await checkPort(port);
    if (!available) {
      log(`⚠️  Port ${port} is in use, cleaning up...`, 'yellow');
      killProcessOnPort(port);
      await new Promise(r => setTimeout(r, 1000)); // Wait for OS to release port
    }

    // Final check
    const isNowAvailable = await checkPort(port);
    if (isNowAvailable) {
      log(`✅ Port ${port} is available`, 'green');
    } else {
      log(`❌ Port ${port} is still blocked. Connection issues may persist.`, 'red');
    }
  }

  log('');
}

async function installDependencies() {
  // Check Node.js dependencies
  if (!fs.existsSync(path.join(__dirname, 'node_modules'))) {
    log('📦 Installing Node.js dependencies...', 'yellow');
    const npmInstall = spawn('npm', ['install'], { stdio: 'inherit', shell: true });
    await new Promise((resolve, reject) => {
      npmInstall.on('close', (code) => {
        if (code === 0) resolve();
        else reject(new Error(`npm install failed with code ${code}`));
      });
    });
    log('');
  }

  // Check client dependencies
  if (!fs.existsSync(path.join(__dirname, 'client', 'node_modules'))) {
    log('📦 Installing React client dependencies...', 'yellow');
    const clientInstall = spawn('npm', ['install'], {
      stdio: 'inherit',
      shell: true,
      cwd: path.join(__dirname, 'client')
    });
    await new Promise((resolve, reject) => {
      clientInstall.on('close', (code) => {
        if (code === 0) resolve();
        else reject(new Error(`client npm install failed with code ${code}`));
      });
    });
    log('');
  }

  // Check Python AI service dependencies
  const aiServicePath = path.join(__dirname, 'ai_service');
  const venvPath = path.join(aiServicePath, 'venv');

  if (!fs.existsSync(venvPath)) {
    log('🐍 Setting up Python virtual environment...', 'yellow');
    const venvCreate = spawn(pythonCmd, ['-m', 'venv', 'venv'], {
      stdio: 'inherit',
      shell: true,
      cwd: aiServicePath
    });
    await new Promise((resolve, reject) => {
      venvCreate.on('close', (code) => {
        if (code === 0) resolve();
        else reject(new Error(`venv creation failed with code ${code}`));
      });
    });

    // Install dependencies in venv
    const pipPath = process.platform === 'win32' ? 'venv\\Scripts\\pip' : 'venv/bin/pip';

    log('📦 Upgrading pip...', 'yellow');
    const pipUpgrade = spawn(pipPath, ['install', '--upgrade', 'pip'], {
      stdio: 'inherit',
      shell: true,
      cwd: aiServicePath
    });
    await new Promise((resolve) => pipUpgrade.on('close', () => resolve()));

    log('📦 Installing AI service dependencies...', 'yellow');
    const requirementsInstall = spawn(pipPath, ['install', '-r', 'requirements.txt'], {
      stdio: 'inherit',
      shell: true,
      cwd: aiServicePath
    });
    await new Promise((resolve, reject) => {
      requirementsInstall.on('close', (code) => {
        if (code === 0 || code === null) resolve();
        else reject(new Error(`pip install failed with code ${code}`));
      });
    });
    log('');
  } else {
    // Verify dependencies are installed
    const pythonExec = process.platform === 'win32'
      ? path.join(venvPath, 'Scripts', 'python.exe')
      : path.join(venvPath, 'bin', 'python3');

    try {
      require('child_process').execSync(`"${pythonExec}" -c "import cv2, flask, ultralytics"`, { stdio: 'ignore' });
    } catch (e) {
      log('📦 Some AI dependencies missing, installing...', 'yellow');
      const pipExec = process.platform === 'win32'
        ? path.join(venvPath, 'Scripts', 'pip.exe')
        : path.join(venvPath, 'bin', 'pip3');

      const pipInstall = spawn(`"${pipExec}"`, ['install', '-r', 'requirements.txt'], {
        stdio: 'inherit',
        shell: true,
        cwd: aiServicePath
      });
      await new Promise((resolve) => pipInstall.on('close', () => resolve()));
    }
  }
}

function startServices() {
  log('🚀 Starting all services...', 'green');
  log('');
  log('Services will be available at:', 'blue');
  log('  • React Frontend: http://localhost:5173', 'green');
  log('  • Node.js Bridge: http://localhost:3001 (HTTP), ws://localhost:3002 (WebSocket)', 'green');
  log('  • AI Service: http://localhost:5001', 'green');
  log('');
  log('Press Ctrl+C to stop all services', 'yellow');
  log('');

  // Check if concurrently is installed
  try {
    require('concurrently');
  } catch {
    log('📦 Installing concurrently...', 'yellow');
    const installConcurrently = spawn('npm', ['install', 'concurrently'], {
      stdio: 'inherit',
      shell: true
    });
    installConcurrently.on('close', () => {
      startConcurrently();
    });
    return;
  }

  startConcurrently();
}

function startConcurrently() {
  const concurrently = require('concurrently');

  const commands = [
    {
      name: 'BRIDGE',
      command: 'node server/index.js',
      prefixColor: 'blue'
    },
    {
      name: 'CLIENT',
      command: `npm run dev`,
      cwd: path.join(__dirname, 'client'),
      prefixColor: 'green'
    },
    {
      name: 'AI',
      command: process.platform === 'win32'
        ? `venv\\Scripts\\python.exe server.py`
        : `source venv/bin/activate && python3 server.py`,
      cwd: path.join(__dirname, 'ai_service'),
      prefixColor: 'yellow'
    }
  ];

  const run = concurrently(commands, {
    killOthers: ['failure', 'success'],
    restartTries: 0,
    prefix: 'name',
    timestampFormat: 'HH:mm:ss',
  });

  const resultPromise = run.result || run;

  if (resultPromise && typeof resultPromise.catch === 'function') {
    resultPromise.catch((error) => {
      if (error && error.message) {
        log(`\n❌ Error starting services: ${error.message}`, 'red');
      }
      process.exit(1);
    });
  }
}

// Main execution
(async () => {
  try {
    await checkPrerequisites();
    await installDependencies();
    startServices();
  } catch (error) {
    log(`\n❌ Error: ${error.message}`, 'red');
    process.exit(1);
  }
})();

