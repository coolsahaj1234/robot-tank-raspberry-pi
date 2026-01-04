# Docker Quick Start Guide

## For Windows Users (4GB RAM)

### Step 1: Install Docker Desktop
1. Download from: https://www.docker.com/products/docker-desktop/
2. Install and restart computer
3. Open Docker Desktop settings
4. Set Memory to **2 GB** (Settings → Resources → Memory)
   - Windows needs 1.5-2GB for the OS
   - This leaves 2-2.5GB for Docker
5. Set Swap to **1 GB** (helps with memory spikes)
6. Click Apply & Restart

### Step 2: Configure Robot IP
```cmd
copy .env.example .env
notepad .env
```
Edit ROBOT_IP to match your robot's IP address (e.g., 10.0.0.86)

### Step 3: Run the Launcher
**Easy Way:**
```cmd
docker-start.bat
```
Then select option 1 or 2 from the menu.

**Manual Way:**
```cmd
REM Option 1: Simple Web Interface (Recommended)
docker-compose up web-robot-controller

REM Option 2: Advanced 3D Dashboard
docker-compose up avs-robot-dashboard
```

### Access the Services
- **Web Robot Controller**: http://localhost:8080
- **AVS Robot Dashboard**: http://localhost:3000

### Stop Services
Press `Ctrl+C` in the terminal, or run:
```cmd
docker-compose down
```

---

## For Mac/Linux Users

### Step 1: Install Docker
**Mac:** Download Docker Desktop from https://www.docker.com/products/docker-desktop/
**Linux:**
```bash
sudo apt-get update
sudo apt-get install docker.io docker-compose
sudo systemctl start docker
sudo usermod -aG docker $USER
```
Log out and back in.

### Step 2: Configure Robot IP
```bash
cp .env.example .env
nano .env
```
Edit ROBOT_IP to match your robot's IP address.

### Step 3: Run the Launcher
**Easy Way:**
```bash
./docker-start.sh
```

**Manual Way:**
```bash
# Option 1: Simple Web Interface
docker-compose up web-robot-controller

# Option 2: Advanced 3D Dashboard
docker-compose up avs-robot-dashboard
```

### Stop Services
Press `Ctrl+C` in the terminal, or run:
```bash
docker-compose down
```

---

## Useful Commands

### View Logs
```bash
docker-compose logs -f
docker-compose logs -f web-robot-controller
docker-compose logs -f avs-robot-dashboard
```

### Check Memory Usage
```bash
docker stats
```

### Rebuild After Code Changes
```bash
docker-compose build
docker-compose up --build
```

### Clean Up to Free Space
```bash
docker system prune -a
```

### Enter Container (Debug)
```bash
docker exec -it web-robot-controller /bin/bash
docker exec -it avs-robot-dashboard /bin/bash
```

---

## Troubleshooting

### "Docker is not running"
- Start Docker Desktop
- Wait for it to fully start (green icon)

### "Out of Memory"
- Run only ONE service at a time
- Close other programs
- Increase Docker memory in Settings

### "Cannot connect to robot"
- Check robot IP with: `ping <ROBOT_IP>`
- Verify .env file has correct IP
- Ensure robot is powered on

### "Port already in use"
- Stop other services: `docker-compose down`
- Or change ports in docker-compose.yml

---

## Memory Usage Comparison

| Component | Memory Required | Notes |
|-----------|----------------|-------|
| Windows OS | ~1.5-2GB | Cannot reduce |
| Available for Docker | ~2-2.5GB | Maximum usable |
| Web Robot Controller | 1.2-1.8GB | ✅ Works on 4GB RAM |
| AVS Robot Dashboard | 1.4-2GB | ⚠️ Tight on 4GB RAM |
| Both Services Together | 2.6-3.8GB | ❌ Will crash on 4GB RAM |

**Critical for 4GB RAM:**
- ✅ **DO:** Run ONE service at a time
- ❌ **DON'T:** Run both services together
- ✅ **DO:** Close Chrome and other heavy apps first
- ❌ **DON'T:** Expect both services to work simultaneously

---

## Next Steps

1. Read the full guide: `DOCKER_README.md`
2. Configure your robot IP in `.env`
3. Run `docker-start.bat` (Windows) or `./docker-start.sh` (Mac/Linux)
4. Access the web interface
5. Start controlling your robot!

---

## Support

- Docker issues: https://docs.docker.com/desktop/
- Robot connection: Check network and firewall
- Memory issues: Run one service at a time
