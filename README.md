# Aether GUI

<p align="center">
  <img src="assets/icon.png" alt="Aether" width="128">
</p>

<p align="center">
  <b>A beautiful graphical interface for the Aether censorship circumvention client.</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-blue?logo=python&logoColor=white" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/customtkinter-5.4+-green" alt="customtkinter">
  <img src="https://img.shields.io/badge/license-GPL--3.0-red" alt="License">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey" alt="Platforms">
</p>

---

## Features

- **⚡ One-Click Connect** — Connect to Aether with a single button press
- **🔄 Multiple Protocols** — MASQUE (HTTP/3), WireGuard, and WARP-in-WARP
- **🔍 Scan Modes** — Balanced, Turbo, Thorough, Stealth, and Ironclad
- **📋 Live Logs** — Real-time colorized log viewer
- **⚙️ Settings** — Configure DNS, IP version, obfuscation, and transport options
- **🔀 Quick Reconnect** — Auto-reconnect to the last known working gateway
- **🌐 Cross-Platform** — Works on Windows, Linux, and macOS
- **🎨 Beautiful Dark UI** — Modern dark theme with smooth animations

## Screenshots

<p align="center">
  <img src="docs/screenshot.png" alt="Screenshot" width="600">
</p>

## Installing

Grab the latest release from the [Releases page](https://github.com/NikanDeveloper56/Aether-Gui/releases):

Each ZIP contains **everything you need** — just extract and run:
```
AetherGUI(.exe)  ← the graphical interface
aether(.exe)     ← the core engine (bundled)
```

### From Source

```bash
git clone https://github.com/NikanDeveloper56/Aether-Gui.git
cd Aether-Gui
pip install -r requirements.txt
python src/aether_gui.py
```

## Building from Source

```bash
pip install customtkinter pyinstaller
pyinstaller --name=AetherGUI --onefile --noconsole --hidden-import=customtkinter src/aether_gui.py
```

## License

GPL-3.0

---

<p align="center">
  Built by <a href="https://NikanDeveloper56.github.io">Nikan (Nikan.Developer)</a>
</p>
