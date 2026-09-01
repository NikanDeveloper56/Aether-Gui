#!/usr/bin/env python3
"""Aether GUI - A beautiful graphical interface for the Aether censorship circumvention client.
Built by Nikan (Nikan.Developer) - nikan.dev
"""

import sys, os, subprocess, threading, time, json, signal

APP_DIR = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, "frozen", False):
    APP_DIR = os.path.dirname(sys.executable)

import customtkinter as ctk
from tkinter import messagebox

VERSION = "1.8.0"

COLORS = {
    "bg": "#0d1117",
    "surface": "#161b22",
    "surface2": "#21262d",
    "accent": "#58a6ff",
    "accent2": "#bc8cff",
    "text": "#c9d1d9",
    "text_muted": "#8b949e",
    "success": "#3fb950",
    "danger": "#f85149",
    "warning": "#d29922",
    "border": "#30363d",
}

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

PROTOCOLS = ["MASQUE (HTTP/3)", "MASQUE (HTTP/2)", "WireGuard", "WARP-in-WARP"]
SCAN_MODES = ["Balanced", "Turbo", "Thorough", "Stealth", "Ironclad"]

class AetherGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Aether")
        self.geometry("800x560")
        self.minsize(700, 500)
        self.configure(fg_color=COLORS["bg"])

        self.connected = False
        self.process = None
        self.connect_time = 0
        self.timer_id = None
        self.last_gateway = None

        self._build_ui()
        self._animate_entry()

    # ── UI ──────────────────────────────────────────────
    def _build_ui(self):
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=180, corner_radius=0, fg_color=COLORS["surface"])
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        ctk.CTkLabel(self.sidebar, text="AETHER", font=("Segoe UI", 22, "bold"),
                      text_color=COLORS["accent"]).pack(pady=(24, 4))
        ctk.CTkLabel(self.sidebar, text=f"v{VERSION}", font=("Segoe UI", 11),
                      text_color=COLORS["text_muted"]).pack()

        ctk.CTkFrame(self.sidebar, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=16, pady=16)

        self.nav_buttons = []
        for name in ["Home", "Logs", "Settings", "About"]:
            btn = ctk.CTkButton(self.sidebar, text=name, anchor="w", height=38, corner_radius=8,
                                fg_color="transparent", text_color=COLORS["text_muted"],
                                hover_color=COLORS["surface2"], font=("Segoe UI", 13),
                                command=lambda n=name: self._switch_page(n))
            btn.pack(fill="x", padx=12, pady=2)
            self.nav_buttons.append((name, btn))

        self.sidebar.pack_propagate(True)
        ctk.CTkLabel(self.sidebar, text="Nikan.Developer\nnikan.dev",
                      font=("Segoe UI", 10), text_color=COLORS["text_muted"]).pack(side="bottom", pady=12)

        # Main area
        self.main = ctk.CTkFrame(self, corner_radius=0, fg_color=COLORS["bg"])
        self.main.pack(side="right", fill="both", expand=True)

        self.pages = {}
        self._build_home()
        self._build_logs()
        self._build_settings()
        self._build_about()
        self._switch_page("Home")

    # ── Home Page ───────────────────────────────────────
    def _build_home(self):
        page = ctk.CTkFrame(self.main, fg_color=COLORS["bg"])
        self.pages["Home"] = page

        # Status card
        card = ctk.CTkFrame(page, fg_color=COLORS["surface"], corner_radius=16, height=180)
        card.pack(fill="x", padx=32, pady=(32, 16))
        card.pack_propagate(False)

        self.status_label = ctk.CTkLabel(card, text="Disconnected", font=("Segoe UI", 28, "bold"),
                                          text_color=COLORS["danger"])
        self.status_label.pack(pady=(24, 4))

        self.timer_label = ctk.CTkLabel(card, text="00:00:00", font=("Consolas", 22),
                                         text_color=COLORS["text_muted"])
        self.timer_label.pack()

        self.conn_info = ctk.CTkLabel(card, text="", font=("Segoe UI", 12),
                                       text_color=COLORS["text_muted"])
        self.conn_info.pack(pady=(4, 0))

        # Connect button
        self.connect_btn = ctk.CTkButton(page, text="⚡  Connect", height=52, corner_radius=14,
                                          font=("Segoe UI", 16, "bold"),
                                          fg_color=COLORS["accent"], hover_color="#2d8cdb",
                                          text_color="#ffffff",
                                          command=self._toggle_connection)
        self.connect_btn.pack(fill="x", padx=32, pady=8)

        self.reconnect_btn = ctk.CTkButton(page, text="🔀  Quick Reconnect", height=40, corner_radius=10,
                                            font=("Segoe UI", 13),
                                            fg_color=COLORS["surface2"], hover_color=COLORS["border"],
                                            text_color=COLORS["text"],
                                            command=self._quick_reconnect)
        self.reconnect_btn.pack(fill="x", padx=32, pady=(0, 16))

        # Options row
        opts = ctk.CTkFrame(page, fg_color=COLORS["surface"], corner_radius=12)
        opts.pack(fill="x", padx=32, pady=(0, 16))

        ctk.CTkLabel(opts, text="Protocol:", font=("Segoe UI", 12),
                      text_color=COLORS["text_muted"]).pack(side="left", padx=(16, 8), pady=12)
        self.protocol_var = ctk.StringVar(value="MASQUE (HTTP/3)")
        ctk.CTkOptionMenu(opts, variable=self.protocol_var, values=PROTOCOLS,
                           width=180, corner_radius=8, fg_color=COLORS["surface2"]).pack(side="left", pady=12)

        ctk.CTkLabel(opts, text="Scan:", font=("Segoe UI", 12),
                      text_color=COLORS["text_muted"]).pack(side="left", padx=(24, 8), pady=12)
        self.scan_var = ctk.StringVar(value="Balanced")
        ctk.CTkOptionMenu(opts, variable=self.scan_var, values=SCAN_MODES,
                           width=130, corner_radius=8, fg_color=COLORS["surface2"]).pack(side="left", pady=12)

        # Quick stats
        stats = ctk.CTkFrame(page, fg_color="transparent")
        stats.pack(fill="x", padx=32, pady=(0, 8))
        self.stat_protocol = self._stat_box(stats, "Protocol", "MASQUE")
        self.stat_port = self._stat_box(stats, "SOCKS5 Port", "1819")
        self.stat_ip = self._stat_box(stats, "IP", "—")

    def _stat_box(self, parent, title, value):
        f = ctk.CTkFrame(parent, fg_color=COLORS["surface"], corner_radius=10, height=70)
        f.pack(side="left", fill="both", expand=True, padx=(0, 8))
        f.pack_propagate(False)
        ctk.CTkLabel(f, text=title, font=("Segoe UI", 10), text_color=COLORS["text_muted"]).pack(pady=(10, 2))
        lbl = ctk.CTkLabel(f, text=value, font=("Segoe UI", 15, "bold"), text_color=COLORS["text"])
        lbl.pack()
        return lbl

    # ── Logs Page ───────────────────────────────────────
    def _build_logs(self):
        page = ctk.CTkFrame(self.main, fg_color=COLORS["bg"])
        self.pages["Logs"] = page

        ctk.CTkLabel(page, text="Logs", font=("Segoe UI", 20, "bold"),
                      text_color=COLORS["text"], anchor="w").pack(fill="x", padx=32, pady=(24, 8))

        self.log_text = ctk.CTkTextbox(page, font=("Consolas", 12), fg_color=COLORS["surface"],
                                        text_color=COLORS["text_muted"], corner_radius=10,
                                        border_width=1, border_color=COLORS["border"])
        self.log_text.pack(fill="both", expand=True, padx=32, pady=(0, 16))
        self.log_text.configure(state="disabled")

        ctk.CTkButton(page, text="🗑  Clear Logs", height=34, corner_radius=8,
                       fg_color=COLORS["surface2"], hover_color=COLORS["border"],
                       text_color=COLORS["text"], command=self._clear_logs).pack(padx=32, pady=(0, 16))

    # ── Settings Page ───────────────────────────────────
    def _build_settings(self):
        page = ctk.CTkFrame(self.main, fg_color=COLORS["bg"])
        self.pages["Settings"] = page

        ctk.CTkLabel(page, text="Settings", font=("Segoe UI", 20, "bold"),
                      text_color=COLORS["text"], anchor="w").pack(fill="x", padx=32, pady=(24, 8))

        # SOCKS5 port
        row = ctk.CTkFrame(page, fg_color=COLORS["surface"], corner_radius=10)
        row.pack(fill="x", padx=32, pady=4)
        ctk.CTkLabel(row, text="SOCKS5 Port", font=("Segoe UI", 13),
                      text_color=COLORS["text"]).pack(side="left", padx=16, pady=12)
        self.port_entry = ctk.CTkEntry(row, width=100, corner_radius=8, fg_color=COLORS["surface2"],
                                        border_color=COLORS["border"], text_color=COLORS["text"])
        self.port_entry.insert(0, "1819")
        self.port_entry.pack(side="right", padx=16, pady=12)

        # Quick reconnect toggle
        row2 = ctk.CTkFrame(page, fg_color=COLORS["surface"], corner_radius=10)
        row2.pack(fill="x", padx=32, pady=4)
        ctk.CTkLabel(row2, text="Quick Reconnect", font=("Segoe UI", 13),
                      text_color=COLORS["text"]).pack(side="left", padx=16, pady=12)
        self.reconnect_toggle = ctk.CTkSwitch(row2, text="", onvalue=True, offvalue=False)
        self.reconnect_toggle.pack(side="right", padx=16, pady=12)
        self.reconnect_toggle.select()

        # TLS Fragmentation
        row3 = ctk.CTkFrame(page, fg_color=COLORS["surface"], corner_radius=10)
        row3.pack(fill="x", padx=32, pady=4)
        ctk.CTkLabel(row3, text="TLS Fragmentation (HTTP/2)", font=("Segoe UI", 13),
                      text_color=COLORS["text"]).pack(side="left", padx=16, pady=12)
        self.tls_toggle = ctk.CTkSwitch(row3, text="", onvalue=True, offvalue=False)
        self.tls_toggle.pack(side="right", padx=16, pady=12)

        # DNS
        row4 = ctk.CTkFrame(page, fg_color=COLORS["surface"], corner_radius=10)
        row4.pack(fill="x", padx=32, pady=4)
        ctk.CTkLabel(row4, text="DNS Servers", font=("Segoe UI", 13),
                      text_color=COLORS["text"]).pack(side="left", padx=16, pady=12)
        self.dns_entry = ctk.CTkEntry(row4, width=200, corner_radius=8, fg_color=COLORS["surface2"],
                                       border_color=COLORS["border"], text_color=COLORS["text"])
        self.dns_entry.insert(0, "1.1.1.1, 1.0.0.1")
        self.dns_entry.pack(side="right", padx=16, pady=12)

        # IP version
        row5 = ctk.CTkFrame(page, fg_color=COLORS["surface"], corner_radius=10)
        row5.pack(fill="x", padx=32, pady=4)
        ctk.CTkLabel(row5, text="IP Version", font=("Segoe UI", 13),
                      text_color=COLORS["text"]).pack(side="left", padx=16, pady=12)
        self.ip_var = ctk.StringVar(value="Dual")
        ctk.CTkOptionMenu(row5, variable=self.ip_var, values=["IPv4", "IPv6", "Dual"],
                           width=100, corner_radius=8, fg_color=COLORS["surface2"]).pack(side="right", padx=16, pady=12)

        # Noize
        row6 = ctk.CTkFrame(page, fg_color=COLORS["surface"], corner_radius=10)
        row6.pack(fill="x", padx=32, pady=4)
        ctk.CTkLabel(row6, text="Noize Profile", font=("Segoe UI", 13),
                      text_color=COLORS["text"]).pack(side="left", padx=16, pady=12)
        self.noize_var = ctk.StringVar(value="Disabled")
        ctk.CTkOptionMenu(row6, variable=self.noize_var,
                           values=["Disabled", "Normal", "Strong"],
                           width=100, corner_radius=8, fg_color=COLORS["surface2"]).pack(side="right", padx=16, pady=12)

        # Save button
        ctk.CTkButton(page, text="💾  Save Settings", height=40, corner_radius=10,
                       fg_color=COLORS["accent"], hover_color="#2d8cdb",
                       text_color="#fff", command=self._save_settings).pack(padx=32, pady=20)

    # ── About Page ──────────────────────────────────────
    def _build_about(self):
        page = ctk.CTkFrame(self.main, fg_color=COLORS["bg"])
        self.pages["About"] = page

        ctk.CTkLabel(page, text="About", font=("Segoe UI", 20, "bold"),
                      text_color=COLORS["text"], anchor="w").pack(fill="x", padx=32, pady=(24, 8))

        card = ctk.CTkFrame(page, fg_color=COLORS["surface"], corner_radius=16)
        card.pack(fill="x", padx=32, pady=8)
        card.pack_propagate(False)
        card.configure(height=280)

        ctk.CTkLabel(card, text="AETHER", font=("Segoe UI", 36, "bold"),
                      text_color=COLORS["accent"]).pack(pady=(28, 2))
        ctk.CTkLabel(card, text=f"Version {VERSION}", font=("Segoe UI", 13),
                      text_color=COLORS["text_muted"]).pack()
        ctk.CTkLabel(card, text="Censorship Circumvention Client",
                      font=("Segoe UI", 14), text_color=COLORS["text"]).pack(pady=(4, 16))

        ctk.CTkFrame(card, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=32)

        ctk.CTkLabel(card, text="GUI built by Nikan (Nikan.Developer)",
                      font=("Segoe UI", 13, "bold"), text_color=COLORS["accent2"]).pack(pady=(16, 4))
        ctk.CTkLabel(card, text="nikan.dev", font=("Segoe UI", 12),
                      text_color=COLORS["text_muted"]).pack()
        ctk.CTkLabel(card, text="Engine by CluvexStudio — t.me/CluvexStudio",
                      font=("Segoe UI", 12), text_color=COLORS["text_muted"]).pack(pady=(12, 0))

        links = ctk.CTkFrame(card, fg_color="transparent")
        links.pack(pady=8)
        for text, url in [("GitHub", "github.com/NikanDeveloper56/aether-gui"),
                           ("Aether Engine", "github.com/CluvexStudio/aether")]:
            ctk.CTkButton(links, text=text, font=("Segoe UI", 11), height=28,
                           corner_radius=6, fg_color=COLORS["surface2"],
                           hover_color=COLORS["border"], text_color=COLORS["accent"],
                           command=lambda u=url: os.startfile(u)).pack(side="left", padx=6)

        ctk.CTkLabel(page, text="This software is provided as-is. Use responsibly.",
                      font=("Segoe UI", 10), text_color=COLORS["text_muted"]).pack(side="bottom", pady=12)

    # ── Navigation ──────────────────────────────────────
    def _switch_page(self, name):
        for page in self.pages.values():
            page.pack_forget()
        self.pages[name].pack(fill="both", expand=True)
        for n, btn in self.nav_buttons:
            if n == name:
                btn.configure(fg_color=COLORS["surface2"], text_color=COLORS["accent"])
            else:
                btn.configure(fg_color="transparent", text_color=COLORS["text_muted"])

    # ── Connection ──────────────────────────────────────
    def _toggle_connection(self):
        if self.connected:
            self._disconnect()
        else:
            self._connect()

    def _connect(self):
        self.connected = True
        self.connect_time = 0
        self.connect_btn.configure(text="⏹  Disconnect", fg_color=COLORS["danger"], hover_color="#c93c42")
        self.status_label.configure(text="Connecting…", text_color=COLORS["warning"])
        self._log("Starting Aether…")

        # Find binary
        binary = None
        for name in ("aether.exe", "aether"):
            for d in (APP_DIR, os.path.join(APP_DIR, "..")):
                p = os.path.join(d, name)
                if os.path.isfile(p):
                    binary = p
                    break
            if binary:
                break

        if not binary:
            self._log("ERROR: aether binary not found. Place it next to the GUI or in PATH.")
            self.status_label.configure(text="Binary not found", text_color=COLORS["danger"])
            self.connected = False
            self.connect_btn.configure(text="⚡  Connect", fg_color=COLORS["accent"], hover_color="#2d8cdb")
            return

        proto = self.protocol_var.get().split("(")[0].strip().lower()
        scan = self.scan_var.get().lower()
        port = self.port_entry.get().strip()

        cmd = [binary, "-s", scan, "-m", "auto", "-w", "socks5://127.0.0.1:" + port]
        if "wireguard" in proto:
            cmd += ["-t", "wg"]
        elif "http/2" in proto:
            cmd += ["-t", "h2"]
        else:
            cmd += ["-t", "h3"]

        if self.reconnect_toggle.get():
            cmd.append("-rc")
        if self.tls_toggle.get():
            cmd += ["-th", "frag"]
        if self.ip_var.get() == "IPv4":
            cmd.append("-4")
        elif self.ip_var.get() == "IPv6":
            cmd.append("-6")
        noize = self.noize_var.get().lower()
        if noize != "disabled":
            cmd += ["-noize", noize]

        self.stat_protocol.configure(text=proto.upper())
        self.stat_port.configure(text=port)
        self._log(f"CMD: {' '.join(cmd)}")

        def run():
            try:
                creationflags = 0
                if sys.platform == "win32":
                    creationflags = subprocess.CREATE_NO_WINDOW
                self.process = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, creationflags=creationflags
                )
                for line in self.process.stdout:
                    self._log(line.rstrip())
                self.process.wait()
            except Exception as e:
                self._log(f"Error: {e}")

            if self.connected:
                self.after(0, lambda: self.status_label.configure(text="Disconnected", text_color=COLORS["danger"]))
                self.connected = False
                self.after(0, lambda: self.connect_btn.configure(
                    text="⚡  Connect", fg_color=COLORS["accent"], hover_color="#2d8cdb"))

        threading.Thread(target=run, daemon=True).start()
        self._start_timer()

    def _disconnect(self):
        self.connected = False
        self._stop_timer()
        if self.process:
            try:
                if sys.platform == "win32":
                    self.process.terminate()
                else:
                    self.process.send_signal(signal.SIGTERM)
            except Exception:
                pass
        self.process = None
        self.status_label.configure(text="Disconnected", text_color=COLORS["danger"])
        self.connect_btn.configure(text="⚡  Connect", fg_color=COLORS["accent"], hover_color="#2d8cdb")
        self.conn_info.configure(text="")
        self.stat_ip.configure(text="—")
        self._log("Disconnected.")

    def _quick_reconnect(self):
        if self.connected:
            self._disconnect()
            time.sleep(0.5)
        self._connect()

    # ── Timer ───────────────────────────────────────────
    def _start_timer(self):
        self.status_label.configure(text="Connected", text_color=COLORS["success"])
        self.connect_time = int(time.time())
        self._tick()

    def _tick(self):
        if not self.connected:
            return
        elapsed = int(time.time()) - self.connect_time
        h, m, s = elapsed // 3600, (elapsed % 3600) // 60, elapsed % 60
        self.timer_label.configure(text=f"{h:02d}:{m:02d}:{s:02d}")
        self.conn_info.configure(text=f"SOCKS5 → 127.0.0.1:{self.port_entry.get().strip()}")
        self.timer_id = self.after(1000, self._tick)

    def _stop_timer(self):
        if self.timer_id:
            self.after_cancel(self.timer_id)
            self.timer_id = None
        self.timer_label.configure(text="00:00:00")

    # ── Logs ────────────────────────────────────────────
    def _log(self, msg):
        def _w():
            self.log_text.configure(state="normal")
            self.log_text.insert("end", msg + "\n")
            self.log_text.see("end")
            self.log_text.configure(state="disabled")
        if threading.current_thread() is threading.main_thread():
            _w()
        else:
            self.after(0, _w)

    def _clear_logs(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    # ── Settings ────────────────────────────────────────
    def _save_settings(self):
        cfg = {
            "port": self.port_entry.get().strip(),
            "quick_reconnect": self.reconnect_toggle.get(),
            "tls_frag": self.tls_toggle.get(),
            "dns": self.dns_entry.get().strip(),
            "ip_version": self.ip_var.get(),
            "noize": self.noize_var.get(),
            "protocol": self.protocol_var.get(),
            "scan": self.scan_var.get(),
        }
        cfg_path = os.path.join(APP_DIR, "aether_gui.json")
        with open(cfg_path, "w") as f:
            json.dump(cfg, f, indent=2)
        self._log(f"Settings saved to {cfg_path}")

    def _load_settings(self):
        cfg_path = os.path.join(APP_DIR, "aether_gui.json")
        if not os.path.isfile(cfg_path):
            return
        try:
            with open(cfg_path) as f:
                cfg = json.load(f)
            self.port_entry.delete(0, "end")
            self.port_entry.insert(0, cfg.get("port", "1819"))
            if cfg.get("quick_reconnect"):
                self.reconnect_toggle.select()
            else:
                self.reconnect_toggle.deselect()
            if cfg.get("tls_frag"):
                self.tls_toggle.select()
            else:
                self.tls_toggle.deselect()
            self.dns_entry.delete(0, "end")
            self.dns_entry.insert(0, cfg.get("dns", "1.1.1.1, 1.0.0.1"))
            self.ip_var.set(cfg.get("ip_version", "Dual"))
            self.noize_var.set(cfg.get("noize", "Disabled"))
            self.protocol_var.set(cfg.get("protocol", "MASQUE (HTTP/3)"))
            self.scan_var.set(cfg.get("scan", "Balanced"))
        except Exception:
            pass

    # ── Entry Animation ─────────────────────────────────
    def _animate_entry(self):
        self.after(10, self._load_settings)
        self.attributes("-alpha", 0.0)
        self._fade_steps = 0
        def _fade():
            self._fade_steps += 1
            alpha = min(1.0, self._fade_steps / 15)
            self.attributes("-alpha", alpha)
            if alpha < 1.0:
                self.after(20, _fade)
        _fade()

    def on_close(self):
        if self.connected:
            self._disconnect()
        self.destroy()

if __name__ == "__main__":
    app = AetherGUI()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
