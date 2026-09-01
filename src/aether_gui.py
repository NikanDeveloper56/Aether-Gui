#!/usr/bin/env python3
"""Aether GUI - A beautiful graphical interface for the Aether censorship circumvention client.
Built by Nikan (Nikan.Developer) - NikanDeveloper56.github.io
"""

import sys, os, subprocess, threading, time, json, signal, socket

APP_DIR = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, "frozen", False):
    APP_DIR = os.path.dirname(sys.executable)

ICON_PATH = os.path.join(APP_DIR, "icon.ico")

import customtkinter as ctk

VERSION = "1.8.0"
MAX_AUTO_RETRIES = 3
RETRY_BACKOFF = [2, 5, 10]  # seconds

# Connection timeouts per scan mode (seconds)
CONNECT_TIMEOUTS = {
    "turbo": 90,
    "balanced": 150,
    "thorough": 330,
    "stealth": 210,
    "ironclad": 240,
}

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

if os.path.isfile(ICON_PATH):
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("nikan.aether.gui")
    except Exception:
        pass

PROTOCOLS = ["MASQUE (HTTP/3)", "MASQUE (HTTP/2)", "WireGuard", "WARP-in-WARP"]
SCAN_MODES = ["Balanced", "Turbo", "Thorough", "Stealth", "Ironclad"]

# State machine
STATE_IDLE = "idle"
STATE_LAUNCHING = "launching"
STATE_CONNECTING = "connecting"
STATE_CONNECTED = "connected"
STATE_RECONNECTING = "reconnecting"
STATE_DISCONNECTING = "disconnecting"
STATE_ERROR = "error"


def port_is_live(host, port, timeout=0.3):
    """Ground truth: can we TCP-connect to the SOCKS5 port?"""
    try:
        sock = socket.create_connection((host, int(port)), timeout=timeout)
        sock.close()
        return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


class AetherGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Aether")
        self.geometry("800x560")
        self.minsize(700, 500)
        self.configure(fg_color=COLORS["bg"])

        if os.path.isfile(ICON_PATH):
            try:
                self.iconbitmap(ICON_PATH)
            except Exception:
                pass

        # State
        self._conn_state = STATE_IDLE
        self.process = None
        self.connect_time = 0
        self.timer_id = None
        self.retry_count = 0
        self.user_requested_stop = False
        self.monitor_thread = None

        self._build_ui()
        self._animate_entry()

    # ── UI ──────────────────────────────────────────────
    def _build_ui(self):
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
        ctk.CTkLabel(self.sidebar, text="Nikan.Developer\nNikanDeveloper56.github.io",
                      font=("Segoe UI", 10), text_color=COLORS["text_muted"]).pack(side="bottom", pady=12)

        self.main = ctk.CTkFrame(self, corner_radius=0, fg_color=COLORS["bg"])
        self.main.pack(side="right", fill="both", expand=True)

        self.pages = {}
        self._build_home()
        self._build_logs()
        self._build_settings()
        self._build_about()
        self._switch_page("Home")

    def _build_home(self):
        page = ctk.CTkFrame(self.main, fg_color=COLORS["bg"])
        self.pages["Home"] = page

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

        self.connect_btn = ctk.CTkButton(page, text="⚡  Connect", height=52, corner_radius=14,
                                          font=("Segoe UI", 16, "bold"),
                                          fg_color=COLORS["accent"], hover_color="#2d8cdb",
                                          text_color="#ffffff",
                                          command=self._on_connect_click)
        self.connect_btn.pack(fill="x", padx=32, pady=8)

        self.reconnect_btn = ctk.CTkButton(page, text="🔀  Quick Reconnect", height=40, corner_radius=10,
                                            font=("Segoe UI", 13),
                                            fg_color=COLORS["surface2"], hover_color=COLORS["border"],
                                            text_color=COLORS["text"],
                                            command=self._quick_reconnect)
        self.reconnect_btn.pack(fill="x", padx=32, pady=(0, 16))

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

    def _build_settings(self):
        page = ctk.CTkFrame(self.main, fg_color=COLORS["bg"])
        self.pages["Settings"] = page
        ctk.CTkLabel(page, text="Settings", font=("Segoe UI", 20, "bold"),
                      text_color=COLORS["text"], anchor="w").pack(fill="x", padx=32, pady=(24, 8))

        row = ctk.CTkFrame(page, fg_color=COLORS["surface"], corner_radius=10)
        row.pack(fill="x", padx=32, pady=4)
        ctk.CTkLabel(row, text="SOCKS5 Port", font=("Segoe UI", 13),
                      text_color=COLORS["text"]).pack(side="left", padx=16, pady=12)
        self.port_entry = ctk.CTkEntry(row, width=100, corner_radius=8, fg_color=COLORS["surface2"],
                                        border_color=COLORS["border"], text_color=COLORS["text"])
        self.port_entry.insert(0, "1819")
        self.port_entry.pack(side="right", padx=16, pady=12)

        row2 = ctk.CTkFrame(page, fg_color=COLORS["surface"], corner_radius=10)
        row2.pack(fill="x", padx=32, pady=4)
        ctk.CTkLabel(row2, text="Quick Reconnect", font=("Segoe UI", 13),
                      text_color=COLORS["text"]).pack(side="left", padx=16, pady=12)
        self.reconnect_toggle = ctk.CTkSwitch(row2, text="", onvalue=True, offvalue=False)
        self.reconnect_toggle.pack(side="right", padx=16, pady=12)
        self.reconnect_toggle.select()

        row3 = ctk.CTkFrame(page, fg_color=COLORS["surface"], corner_radius=10)
        row3.pack(fill="x", padx=32, pady=4)
        ctk.CTkLabel(row3, text="TLS Fragmentation (HTTP/2)", font=("Segoe UI", 13),
                      text_color=COLORS["text"]).pack(side="left", padx=16, pady=12)
        self.tls_toggle = ctk.CTkSwitch(row3, text="", onvalue=True, offvalue=False)
        self.tls_toggle.pack(side="right", padx=16, pady=12)

        row4 = ctk.CTkFrame(page, fg_color=COLORS["surface"], corner_radius=10)
        row4.pack(fill="x", padx=32, pady=4)
        ctk.CTkLabel(row4, text="DNS Servers", font=("Segoe UI", 13),
                      text_color=COLORS["text"]).pack(side="left", padx=16, pady=12)
        self.dns_entry = ctk.CTkEntry(row4, width=200, corner_radius=8, fg_color=COLORS["surface2"],
                                       border_color=COLORS["border"], text_color=COLORS["text"])
        self.dns_entry.insert(0, "1.1.1.1, 1.0.0.1")
        self.dns_entry.pack(side="right", padx=16, pady=12)

        row5 = ctk.CTkFrame(page, fg_color=COLORS["surface"], corner_radius=10)
        row5.pack(fill="x", padx=32, pady=4)
        ctk.CTkLabel(row5, text="IP Version", font=("Segoe UI", 13),
                      text_color=COLORS["text"]).pack(side="left", padx=16, pady=12)
        self.ip_var = ctk.StringVar(value="Dual")
        ctk.CTkOptionMenu(row5, variable=self.ip_var, values=["IPv4", "IPv6", "Dual"],
                           width=100, corner_radius=8, fg_color=COLORS["surface2"]).pack(side="right", padx=16, pady=12)

        row6 = ctk.CTkFrame(page, fg_color=COLORS["surface"], corner_radius=10)
        row6.pack(fill="x", padx=32, pady=4)
        ctk.CTkLabel(row6, text="Noize Profile", font=("Segoe UI", 13),
                      text_color=COLORS["text"]).pack(side="left", padx=16, pady=12)
        self.noize_var = ctk.StringVar(value="Disabled")
        ctk.CTkOptionMenu(row6, variable=self.noize_var,
                           values=["Disabled", "Light", "Balanced", "Aggressive"],
                           width=120, corner_radius=8, fg_color=COLORS["surface2"]).pack(side="right", padx=16, pady=12)

        ctk.CTkButton(page, text="💾  Save Settings", height=40, corner_radius=10,
                       fg_color=COLORS["accent"], hover_color="#2d8cdb",
                       text_color="#fff", command=self._save_settings).pack(padx=32, pady=20)

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
        ctk.CTkLabel(card, text="NikanDeveloper56.github.io", font=("Segoe UI", 12),
                      text_color=COLORS["text_muted"]).pack()
        ctk.CTkLabel(card, text="",
                      font=("Segoe UI", 12), text_color=COLORS["text_muted"]).pack(pady=(12, 0))
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

    # ── State Machine ───────────────────────────────────
    def _set_state(self, new_state, info=""):
        old = self._conn_state
        self._conn_state = new_state

        if new_state == STATE_IDLE:
            self.status_label.configure(text="Disconnected", text_color=COLORS["danger"])
            self.connect_btn.configure(text="⚡  Connect", fg_color=COLORS["accent"], hover_color="#2d8cdb")
            self.conn_info.configure(text="")
            self.stat_ip.configure(text="—")
            self._stop_timer()

        elif new_state == STATE_LAUNCHING:
            self.status_label.configure(text="Launching…", text_color=COLORS["warning"])
            self.connect_btn.configure(text="⏹  Cancel", fg_color=COLORS["danger"], hover_color="#c93c42")

        elif new_state == STATE_CONNECTING:
            self.status_label.configure(text="Connecting…", text_color=COLORS["warning"])
            self.conn_info.configure(text=f"Scanning for routes ({self.scan_var.get()})…")

        elif new_state == STATE_CONNECTED:
            self.status_label.configure(text="Connected", text_color=COLORS["success"])
            self.connect_btn.configure(text="⏹  Disconnect", fg_color=COLORS["danger"], hover_color="#c93c42")
            self.conn_info.configure(text=f"SOCKS5 → 127.0.0.1:{self.port_entry.get().strip()}")
            self._start_timer()

        elif new_state == STATE_RECONNECTING:
            attempt = info
            self.status_label.configure(text=f"Reconnecting… ({attempt}/{MAX_AUTO_RETRIES})",
                                          text_color=COLORS["warning"])

        elif new_state == STATE_DISCONNECTING:
            self.status_label.configure(text="Disconnecting…", text_color=COLORS["warning"])
            self.connect_btn.configure(text="⏹  Disconnect", fg_color=COLORS["danger"], hover_color="#c93c42")

        elif new_state == STATE_ERROR:
            self.status_label.configure(text=info or "Error", text_color=COLORS["danger"])
            self.connect_btn.configure(text="⚡  Connect", fg_color=COLORS["accent"], hover_color="#2d8cdb")
            self.conn_info.configure(text="")
            self._stop_timer()

    # ── Connect Logic ───────────────────────────────────
    def _on_connect_click(self):
        if self._conn_state in (STATE_IDLE, STATE_ERROR):
            self._start_connect()
        elif self._conn_state in (STATE_LAUNCHING, STATE_CONNECTING, STATE_CONNECTED, STATE_RECONNECTING):
            self._request_disconnect()

    def _find_binary(self):
        for name in ("aether.exe", "aether"):
            for d in (APP_DIR, os.path.join(APP_DIR, "..")):
                p = os.path.join(d, name)
                if os.path.isfile(p):
                    return p
        return None

    def _build_cmd(self, binary):
        proto = self.protocol_var.get()
        scan = self.scan_var.get().lower()
        port = self.port_entry.get().strip()

        cmd = [binary, "--bind", f"127.0.0.1:{port}", "--scan", scan]

        if "WireGuard" in proto:
            cmd.append("--wg")
        elif "HTTP/2" in proto:
            cmd.append("--h2")
        elif "WARP-in-WARP" in proto:
            cmd.append("--gool")
        else:
            cmd.append("--masque")

        if self.reconnect_toggle.get():
            cmd.append("--quick-reconnect")
        if self.tls_toggle.get():
            cmd.append("--fragment")

        ip = self.ip_var.get()
        if ip == "IPv4":
            cmd.append("-4")
        elif ip == "IPv6":
            cmd.append("-6")

        noize = self.noize_var.get().lower()
        if noize != "disabled":
            cmd += ["--noize", noize]

        dns = self.dns_entry.get().strip()
        if dns:
            cmd += ["--dns", dns]

        return cmd

    def _start_connect(self):
        binary = self._find_binary()
        if not binary:
            self._set_state(STATE_ERROR, "Binary not found")
            self._log("ERROR: aether binary not found. Place it next to the GUI or in PATH.")
            return

        cmd = self._build_cmd(binary)
        port = self.port_entry.get().strip()

        self.user_requested_stop = False
        self.retry_count = 0
        self._set_state(STATE_LAUNCHING)
        self._log(f"CMD: {' '.join(cmd)}")

        # Check port is not already in use
        if port_is_live("127.0.0.1", port):
            self._log(f"Port {port} already in use. Is another instance running?")
            self._set_state(STATE_ERROR, f"Port {port} in use")
            return

        # Spawn process
        try:
            creationflags = 0
            if sys.platform == "win32":
                creationflags = subprocess.CREATE_NO_WINDOW
            self.process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, creationflags=creationflags
            )
        except Exception as e:
            self._log(f"Failed to start: {e}")
            self._set_state(STATE_ERROR, str(e))
            return

        # Start log reader thread
        threading.Thread(target=self._read_logs, daemon=True).start()

        # Start monitor thread (the core mechanism)
        self.monitor_thread = threading.Thread(
            target=self._monitor_connect, args=(cmd, port), daemon=True
        )
        self.monitor_thread.start()

    def _read_logs(self):
        """Forward aether output to log panel."""
        try:
            for line in self.process.stdout:
                self._log(line.rstrip())
        except Exception:
            pass

    def _monitor_connect(self, cmd, port):
        """
        Core connection monitor:
        1. Wait for prompts to be answered (Launching → Connecting)
        2. Poll SOCKS5 port every 400ms
        3. If port is live → Connected
        4. If process exits before connecting → auto-retry
        5. If timeout → auto-retry
        """
        scan = self.scan_var.get().lower()
        timeout = CONNECT_TIMEOUTS.get(scan, 150)
        deadline = time.time() + timeout
        announced_connecting = False

        while True:
            time.sleep(0.4)

            if self.user_requested_stop:
                return

            # Check if process exited
            if self.process and self.process.poll() is not None:
                rc = self.process.returncode
                self._log(f"Process exited with code {rc}")
                self._handle_failure(cmd, port, f"Process exited (code {rc})")
                return

            # Transition to Connecting after a brief delay (simulates "prompts done")
            if not announced_connecting and time.time() > deadline - timeout + 3:
                self.after(0, lambda: self._set_state(STATE_CONNECTING))
                announced_connecting = True

            # Ground truth: is the SOCKS5 port alive?
            if port_is_live("127.0.0.1", port):
                self._log(f"SOCKS5 port {port} is live — connected!")
                self.after(0, lambda: self._set_state(STATE_CONNECTED))
                self.retry_count = 0
                # Monitor for unexpected drops
                self._monitor_connected(cmd, port)
                return

            # Timeout check
            if time.time() >= deadline:
                self._log(f"Timeout after {timeout}s waiting for route")
                if self.process:
                    try:
                        self.process.terminate()
                    except Exception:
                        pass
                self._handle_failure(cmd, port, f"Timeout ({timeout}s)")
                return

    def _monitor_connected(self, cmd, port):
        """Watch for unexpected process exit while connected."""
        while True:
            time.sleep(0.5)
            if self.user_requested_stop:
                return
            if self.process and self.process.poll() is not None:
                rc = self.process.returncode
                self._log(f"Connection lost (exit code {rc})")
                self._handle_failure(cmd, port, f"Lost connection (code {rc})")
                return

    def _handle_failure(self, cmd, port, message):
        """Auto-retry with backoff (max 3 attempts)."""
        if self.user_requested_stop:
            self.after(0, lambda: self._set_state(STATE_IDLE))
            return

        self.retry_count += 1
        if self.retry_count > MAX_AUTO_RETRIES:
            self._log(f"Gave up after {MAX_AUTO_RETRIES} retries")
            self.after(0, lambda: self._set_state(STATE_ERROR, f"{message} (gave up after {MAX_AUTO_RETRIES} retries)"))
            return

        attempt = self.retry_count
        self._log(f"Retrying in {RETRY_BACKOFF[attempt-1]}s (attempt {attempt}/{MAX_AUTO_RETRIES})")
        self.after(0, lambda a=attempt: self._set_state(STATE_RECONNECTING, a))

        backoff = RETRY_BACKOFF[attempt - 1]

        def retry_after():
            time.sleep(backoff)
            if self.user_requested_stop:
                return
            self.after(0, lambda: self._set_state(STATE_LAUNCHING))
            # Spawn fresh process
            try:
                creationflags = 0
                if sys.platform == "win32":
                    creationflags = subprocess.CREATE_NO_WINDOW
                self.process = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, creationflags=creationflags
                )
            except Exception as e:
                self._log(f"Retry failed: {e}")
                self.after(0, lambda: self._set_state(STATE_ERROR, str(e)))
                return
            threading.Thread(target=self._read_logs, daemon=True).start()
            threading.Thread(target=self._monitor_connect, args=(cmd, port), daemon=True).start()

        threading.Thread(target=retry_after, daemon=True).start()

    def _request_disconnect(self):
        self.user_requested_stop = True
        self._set_state(STATE_DISCONNECTING)
        self._log("Disconnecting…")

        if self.process:
            try:
                if sys.platform == "win32":
                    self.process.terminate()
                else:
                    self.process.send_signal(signal.SIGTERM)
            except Exception:
                pass

        # Wait up to 3 seconds for graceful shutdown
        def wait_exit():
            start = time.time()
            while time.time() - start < 3:
                if self.process and self.process.poll() is not None:
                    break
                time.sleep(0.2)
            # Force kill if still alive
            if self.process and self.process.poll() is None:
                try:
                    self.process.kill()
                except Exception:
                    pass
            self.process = None
            self.after(0, lambda: self._set_state(STATE_IDLE))
            self._log("Disconnected.")

        threading.Thread(target=wait_exit, daemon=True).start()

    def _quick_reconnect(self):
        if self._conn_state not in (STATE_IDLE, STATE_ERROR):
            self._request_disconnect()
            time.sleep(1)
        self._start_connect()

    # ── Timer ───────────────────────────────────────────
    def _start_timer(self):
        self.connect_time = int(time.time())
        self._tick()

    def _tick(self):
        if self._conn_state != STATE_CONNECTED:
            return
        elapsed = int(time.time()) - self.connect_time
        h, m, s = elapsed // 3600, (elapsed % 3600) // 60, elapsed % 60
        self.timer_label.configure(text=f"{h:02d}:{m:02d}:{s:02d}")
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
        self._log(f"Settings saved.")

    def _load_settings(self):
        cfg_path = os.path.join(APP_DIR, "aether_gui.json")
        if not os.path.isfile(cfg_path):
            return
        try:
            with open(cfg_path) as f:
                cfg = json.load(f)
            self.port_entry.delete(0, "end")
            self.port_entry.insert(0, cfg.get("port", "1819"))
            if cfg.get("quick_reconnect"): self.reconnect_toggle.select()
            else: self.reconnect_toggle.deselect()
            if cfg.get("tls_frag"): self.tls_toggle.select()
            else: self.tls_toggle.deselect()
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
        self.user_requested_stop = True
        if self.process:
            try:
                self.process.kill()
            except Exception:
                pass
        self.destroy()


if __name__ == "__main__":
    app = AetherGUI()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
