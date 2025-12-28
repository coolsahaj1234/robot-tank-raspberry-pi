# Installing Required Packages on Raspberry Pi

## For LED Control (PCB v2)

Since newer Raspberry Pi OS versions use externally-managed Python environments, use `apt` instead of `pip3`:

```bash
sudo apt-get update
<<<<<<< HEAD
sudo apt-get install python3-numpy python3-spidev
=======
sudo apt-get install python3-numpy python3-spidev python3-smbus
>>>>>>> 40885bf (Initial commit)
```

## Alternative: Using pip3 with --break-system-packages

If apt packages are not available or outdated, you can use pip3 with the override flag:

```bash
<<<<<<< HEAD
sudo pip3 install --break-system-packages numpy spidev
=======
sudo pip3 install --break-system-packages numpy spidev smbus2
>>>>>>> 40885bf (Initial commit)
```

**Note**: The `--break-system-packages` flag bypasses Python's protection mechanism. Use with caution, but it's generally safe for system-level packages like numpy and spidev on Raspberry Pi.

## Verify Installation

Check if packages are installed:
```bash
python3 -c "import numpy; print('numpy:', numpy.__version__)"
python3 -c "import spidev; print('spidev: OK')"
<<<<<<< HEAD
=======
python3 -c "import smbus; print('smbus: OK')"
>>>>>>> 40885bf (Initial commit)
```

## Complete LED Setup Checklist

<<<<<<< HEAD
1. ✅ Install packages: `sudo apt-get install python3-numpy python3-spidev`
2. ✅ Enable SPI: `sudo raspi-config` → Interface Options → SPI → Enable
=======
1. ✅ Install packages: `sudo apt-get install python3-numpy python3-spidev python3-smbus`
2. ✅ Enable SPI & I2C: `sudo raspi-config` → Interface Options → SPI/I2C → Enable
>>>>>>> 40885bf (Initial commit)
3. ✅ Reboot: `sudo reboot`
4. ✅ Test: `sudo python test.py led`

## Troubleshooting

### If apt packages are not found:
```bash
sudo apt-get update
sudo apt-get install python3-numpy python3-spidev
```

### If you get "package not available" errors:
Try installing from pip3 with the override flag:
```bash
sudo pip3 install --break-system-packages numpy spidev
```

### Verify SPI is enabled:
```bash
ls /dev/spi*
```
Should show `/dev/spidev0.0` and `/dev/spidev0.1`

### Check SPI in config:
```bash
grep spi /boot/firmware/config.txt
```
Should show `dtparam=spi=on`

