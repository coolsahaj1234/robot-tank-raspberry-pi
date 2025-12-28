#!/bin/bash

# --- Robot Tank Integrated Test & Setup Script ---
# This script installs dependencies and provides a menu for hardware testing.

# Text colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Robot Tank: Integrated Test & Setup ===${NC}"

# 1. Dependency Installation
echo -e "\n${BLUE}[1] Checking Dependencies...${NC}"
read -p "Do you want to install/update dependencies? (y/n): " install_deps
if [[ $install_deps == "y" || $install_deps == "Y" ]]; then
    echo -e "${GREEN}Updating package list...${NC}"
    sudo apt-get update
    echo -e "${GREEN}Installing Python libraries and I2C tools...${NC}"
    sudo apt-get install -y python3-numpy python3-spidev python3-smbus python3-gpiozero python3-pigpio i2c-tools pigpio
    
    echo -e "${GREEN}Enabling I2C and SPI interfaces...${NC}"
    sudo raspi-config nonint do_i2c 0
    sudo raspi-config nonint do_spi 0
    
    echo -e "${GREEN}Ensuring pigpio daemon is running...${NC}"
    sudo systemctl enable pigpiod
    sudo systemctl start pigpiod
    
    echo -e "${GREEN}Dependencies installation and interface activation complete.${NC}"
    echo -e "${RED}Please reboot if this is the first time enabling I2C/SPI: sudo reboot${NC}"
else
    echo "Skipping dependency installation."
fi

# 1.1 Pre-check I2C
if [[ ! -e /dev/i2c-1 ]]; then
    echo -e "${RED}WARNING: /dev/i2c-1 not found!${NC}"
    echo -e "Please ensure I2C is enabled and you have rebooted."
fi

# 2. Hardware Test Menu
while true; do
    echo -e "\n${BLUE}=== Hardware Test Menu ===${NC}"
    echo "1) Test Parameters (Hardware Info)"
    echo "2) Test LEDs (RGB Breath/Flash)"
    echo "3) Test Motors (Forward/Backward/Turn)"
    echo "4) Test Ultrasonic (Front & Back Distance)"
    echo "5) Test Infrared (Line Sensors)"
    echo "6) Test Servos (Pan/Tilt)"
    echo "7) Test IMU (MPU6050 Orientation)"
    echo "8) Test Camera (Capture Image)"
    echo "9) Start Tank Server (Headless)"
    echo "0) Exit"
    read -p "Select an option [0-9]: " opt

    case $opt in
        1) sudo python3 test.py parameter ;;
        2) sudo python3 test.py led ;;
        3) sudo python3 test.py motor ;;
        4) sudo python3 test.py ultrasonic ;;
        5) sudo python3 test.py infrared ;;
        6) sudo python3 test.py servo ;;
        7) sudo python3 test.py imu ;;
        8) sudo python3 test.py camera ;;
        9) 
            echo -e "${GREEN}Starting headless server...${NC}"
            sudo python3 server_headless.py
            ;;
        0) 
            echo -e "${BLUE}Exiting...${NC}"
            exit 0 
            ;;
        *) echo -e "${RED}Invalid option. Please try again.${NC}" ;;
    esac
done
