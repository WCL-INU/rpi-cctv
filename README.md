# RPi CCTV System

## 📋 Overview
A multi-camera CCTV surveillance system based on Raspberry Pi. Designed with a client-server architecture, it enables multiple RPi clients to capture video footage and transmit it to a central server for management and storage.

---

## 🎯 Project Goals
- Build a cost-effective CCTV system
- Manage distributed camera nodes
- Centralized video storage and management

---

## Project Architecture

* **Client (Raspberry Pi)**
  - Captures video using the Raspberry Pi Camera
  - Records video in 2-minute segments
  - temporarily stores videos locally use RAM disk to minimize SD card wear
* **Server (Ubuntu)**
  - Collects video files from multiple RPi clients via SSH and rsync
  - Uses multithreading to handle multiple clients concurrently
  - Uses a SSH config file for easy host management
  - Organizes videos by host and date
  - Provides a foundation for future video management features

---

## 📁 Project Structure
```
rpi-cctv/
├── README.md                          # Project documentation
├── Client/                            # Raspberry Pi client
│   ├── setup.sh                       # Client setup script
│   ├── record.sh                      # Video recording script
│   └── rpi-cctv-client.service        # systemd service file
└── Server/                            # Central server
    ├── setup.sh                       # Server setup script
    ├── config.yaml                    # Configuration file with host aliases
    ├── collect_cctv.py                # Main video collection script
    ├── rpi-cctv-server.service        # systemd service file
    └── rpi-cctv-server.timer          # systemd timer for scheduled collection

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
- **OS**: Ubuntu 24.04.3 LTS
- **CPU**: Intel(R) Celeron(R) J4005 CPU @ 2.00GHz
- **RAM**: 4GB

---

## 🚀 Installation & Setup

### Client Setup
```bash
sudo ./Client/setup.sh
```

### Server Setup
This system uses `Host Alias` instead of IP addresses. You need to configure the `~/.ssh/config` file. 
also, edit the `Server/config.yaml` file to add your host aliases. this file generated automatically when you run the setup script.
```bash
sudo ./Server/setup.sh
```

---

## 📝 Common Commands
- **Client Side**

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

- **Server Side**

    ### Check Collection Status
    ```bash
    sudo systemctl status rpi-cctv-server.service
    ```

    ### View Logs
    ```bash
    sudo journalctl -u rpi-cctv-server.service -f
    ```

    ### Restart Service
    ```bash
    sudo systemctl restart rpi-cctv-server.service
    ```

    ### Check Collection Timer
    ```bash
    sudo systemctl status rpi-cctv-server.timer
    ```

---

## 📚 References
- [Raspberry Pi Camera Software Official Documentation](https://www.raspberrypi.com/documentation/computers/camera_software.html)

---

## 📄 License
MIT License

