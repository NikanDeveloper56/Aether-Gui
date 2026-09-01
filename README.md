# Aether GUI

<p align="center">
  <img src="assets/banner.png" alt="Aether" width="600">
</p>

<p align="center">
  <b>A beautiful graphical interface for the <a href="https://github.com/CluvexStudio/aether">Aether</a> censorship circumvention client.</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-blue?logo=python&logoColor=white" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/PySide6-6.5+-green?logo=qt&logoColor=white" alt="PySide6">
  <img src="https://img.shields.io/badge/license-GPL--3.0-red" alt="License">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey" alt="Platforms">
</p>

---

## Features

- **🎨 Beautiful Dark UI** — Modern dark theme with smooth animations and branded design
- **⚡ One-Click Connect** — Connect to Aether with a single button press
- **🔄 Multiple Protocols** — MASQUE (HTTP/3), WireGuard, and WARP-in-WARP
- **🔍 Scan Modes** — Balanced, Turbo, Thorough, Stealth, and Ironclad
- **📋 Live Logs** — Real-time colorized log viewer
- **⚙️ Settings** — Configure DNS, IP version, obfuscation, and transport options
- **🔀 Quick Reconnect** — Auto-reconnect to the last known working gateway
- **🌐 Cross-Platform** — Works on Windows, Linux, and macOS

## Screenshots

<p align="center">
  <img src="assets/screenshot-home.png" alt="Home" width="400">
  <img src="assets/screenshot-logs.png" alt="Logs" width="400">
</p>

## Requirements

- Python 3.10 or later
- [Aether](https://github.com/CluvexStudio/aether) binary (v1.8.0+)
- PySide6

## Installation

### From Release (Recommended)

1. Download the latest release for your platform from [Releases](https://github.com/NikanDeveloper56/aether-gui/releases)
2. Place the `aether` binary in the same directory as the GUI
3. Run the application

### From Source

```bash
git clone https://github.com/NikanDeveloper56/aether-gui.git
cd aether-gui

# Install dependencies
pip install -r requirements.txt

# Run
python src/aether_gui.py
```

## Usage

1. Place the `aether` binary (or `aether.exe` on Windows) in the same directory as the GUI, or ensure it's in your PATH
2. Launch the GUI:
   ```bash
   python src/aether_gui.py
   ```
3. Select your preferred protocol (MASQUE, WireGuard, or WARP-in-WARP)
4. Choose a scan mode
5. Click **⚡ Connect**

## Configuration

The GUI wraps the Aether CLI and exposes its options through the interface:

| Setting | Description |
|---------|-------------|
| **Protocol** | MASQUE (HTTP/3), WireGuard, or WARP-in-WARP |
| **Scan Mode** | How aggressively to search for reachable endpoints |
| **SOCKS5 Port** | Local proxy port (default: 1819) |
| **Quick Reconnect** | Auto-reconnect to the last working gateway |
| **TLS Fragmentation** | Fragment ClientHello on HTTP/2 transport |
| **DNS Servers** | Resolvers used inside the tunnel |
| **IP Version** | IPv4, IPv6, or Dual |
| **Noize Profile** | Obfuscation level |

## Building a Standalone Executable

```bash
pip install pyinstaller
pyinstaller --name=AetherGUI --onefile --noconsole --icon=assets/icon.ico src/aether_gui.py
```

## Project Structure

```
aether-gui/
├── src/
│   └── aether_gui.py       # Main GUI application
├── assets/
│   └── icon.ico             # Application icon
├── .github/
│   └── workflows/
│       └── release.yml      # CI/CD for multi-platform releases
├── requirements.txt
├── LICENSE
└── README.md
```

## Credits

- **[Aether](https://github.com/CluvexStudio/aether)** by [CluvexStudio](https://t.me/CluvexStudio) — The core censorship circumvention engine
- **GUI built by [Nikan (Nikan.Developer)](https://nikan.dev)**

## License

This project is licensed under the GPL-3.0 License — see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Built with ❤️ by <a href="https://nikan.dev">Nikan.Developer</a>
</p>
