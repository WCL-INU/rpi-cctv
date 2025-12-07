# RPi CCTV System

## 📋 Overview
A multi-camera CCTV surveillance system based on Raspberry Pi. Designed with a client-server architecture, it enables multiple RPi clients to capture video footage and transmit it to a central server for management and storage.

---

## 🎯 Project Goals
- Build a cost-effective CCTV system
- Manage distributed camera nodes
- Centralized video storage and management

---

## 📁 Project Structure
```
rpi-cctv/
├── README.md                          # Project documentation
├── Client/                            # Raspberry Pi client
│   ├── record.sh                      # Video recording script
│   ├── setup.sh                       # Client setup script
│   └── rpi-cctv-client.service        # systemd service file
└── Server/                            # Central server
    └── (Server code)
```

---

## 🖥️ Tested & Verified Environment

### Client (Raspberry Pi)
- **Hardware**: Raspberry Pi 4B
- **RAM**: 2GB
- **Storage**: 16GB microSD card
- **Camera**: Raspberry Pi Camera v2
- **OS**: Raspberry Pi OS (Bookworm)

### Server
- **OS**:
- **CPU**:
- **RAM**:
- **Storage**:
- **Network**:

---

## 🚀 Installation & Setup

### Client Setup
```bash
chmod +x Client/setup.sh
sudo ./Client/setup.sh
```

### Server Setup
```bash
# Server setup commands (to be added)
```

---

## 📝 Common Commands

### Check Recording Status
```bash
sudo systemctl status rpi-cctv-client
```

### View Logs
```bash
sudo journalctl -u rpi-cctv-client -f
```

### Restart Service
```bash
sudo systemctl restart rpi-cctv-client
```

---

## 📚 References
- [Raspberry Pi Camera Software Official Documentation](https://www.raspberrypi.com/documentation/computers/camera_software.html)

---

## 📄 License
MIT License

