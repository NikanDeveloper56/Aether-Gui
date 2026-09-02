#!/usr/bin/env python3
"""Aether GUI - Beautiful animated interface for the Aether censorship circumvention client.
Built by Nikan (Nikan.Developer) - NikanDeveloper56.github.io
Animations inspired by MatinSenPai/Aether-GUI & QW-AI-Code/Aether
"""

import sys, os, subprocess, threading, time, json, signal, socket, struct, math, random

APP_DIR = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, "frozen", False):
    APP_DIR = os.path.dirname(sys.executable)

ICON_PATH = os.path.join(APP_DIR, "icon.ico")

import customtkinter as ctk

VERSION = "1.8.0"
MAX_AUTO_RETRIES = 3
RETRY_BACKOFF = [2, 5, 10]

CONNECT_TIMEOUTS = {
    "turbo": 90, "balanced": 150, "thorough": 330,
    "stealth": 210, "ironclad": 240,
}

# ── Color palette (orange theme, matching reference) ──
COLORS = {
    "bg": "#0d0d0f",
    "surface": "#1a1a1a",
    "surface2": "#1e1e1e",
    "surface3": "#242424",
    "surface4": "#2a2a2a",
    "accent": "#f2711c",
    "accent2": "#fb923c",
    "accent_glow": "#f2711c40",
    "text": "#f2f2f2",
    "text_muted": "#a3a3a3",
    "success": "#2dd4bf",
    "success_glow": "#2dd4bf40",
    "danger": "#ef4444",
    "danger_glow": "#ef444440",
    "warning": "#f97316",
    "connecting": "#f2711c",
    "connecting_glow": "#f2711c40",
    "border": "#2a2a2a",
    "orbital": "#f2711c",
    "portal": "#111113",
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

STATE_IDLE = "idle"
STATE_LAUNCHING = "launching"
STATE_CONNECTING = "connecting"
STATE_CONNECTED = "connected"
STATE_RECONNECTING = "reconnecting"
STATE_DISCONNECTING = "disconnecting"
STATE_ERROR = "error"


def port_is_live(host, port, timeout=0.3):
    try:
        sock = socket.create_connection((host, int(port)), timeout=timeout)
        sock.close()
        return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


# ══════════════════════════════════════════════════════════
# Animated Connect Portal — breathing, ripple, glow
# ══════════════════════════════════════════════════════════
class ConnectPortal(ctk.CTkCanvas):
    """Circular connect button with breathing glow, ripple rings, and state icons."""

    def __init__(self, parent, size=160, on_click=None, **kwargs):
        super().__init__(parent, width=size, height=size,
                         highlightthickness=0, bg=COLORS["bg"], **kwargs)
        self.size = size
        self.cx = size // 2
        self.cy = size // 2
        self.base_r = size // 2 - 12
        self.on_click = on_click
        self.state = STATE_IDLE
        self._anim_id = None
        self._breath_phase = 0.0
        self._breath_speed = 0.06  # radians per frame (~33ms)
        self._angle = 0.0
        self._sweep = 0.0
        self._ripple_rings = []     # [(radius, alpha, color)]
        self._ripple_next = 0.0
        self._particles = []        # ambient floating particles
        self._shake_x = 0.0
        self._shake_decay = 0.92
        self._glow_alpha = 0.0
        self._glow_target = 0.3
        self._icon_scale = 1.0
        self._icon_target = 1.0

        # Init ambient particles
        for _ in range(8):
            self._particles.append({
                "x": random.uniform(0, size),
                "y": random.uniform(0, size),
                "vx": random.uniform(-0.3, 0.3),
                "vy": random.uniform(-0.4, -0.1),
                "r": random.uniform(1, 3),
                "alpha": random.uniform(0.1, 0.4),
                "color": random.choice(["#f2711c", "#2dd4bf", "#a3a3a3"]),
            })

        self.bind("<Button-1>", self._clicked)

    def set_state(self, state):
        if state == self.state:
            return
        old = self.state
        self.state = state

        if state in (STATE_LAUNCHING, STATE_CONNECTING, STATE_RECONNECTING):
            self._glow_target = 0.8
            self._breath_speed = 0.12
            self._icon_target = 1.0
            # Spawn initial ripples
            self._spawn_ripple(COLORS["connecting"])
        elif state == STATE_CONNECTED:
            self._glow_target = 1.0
            self._breath_speed = 0.05
            self._icon_target = 1.0
            self._spawn_ripple(COLORS["success"])
            self._spawn_ripple(COLORS["success"])
        elif state == STATE_ERROR:
            self._glow_target = 0.6
            self._breath_speed = 0.0
            self._icon_target = 1.0
            self._shake_x = 12.0
            self._spawn_ripple(COLORS["danger"])
        elif state == STATE_DISCONNECTING:
            self._glow_target = 0.4
            self._breath_speed = 0.08
        else:  # idle
            self._glow_target = 0.3
            self._breath_speed = 0.06
            self._icon_target = 1.0

    def _spawn_ripple(self, color):
        self._ripple_rings.append({
            "r": self.base_r,
            "alpha": 0.6,
            "color": color,
            "speed": 1.8,
        })

    def start(self):
        self._tick()

    def stop(self):
        if self._anim_id:
            self.after_cancel(self._anim_id)
            self._anim_id = None

    def _clicked(self, event):
        if self.on_click:
            self.on_click()
            self._spawn_ripple(COLORS["accent"])

    def _tick(self):
        self._breath_phase += self._breath_speed
        self._angle = (self._angle + 2.0) % 360

        # Sweep for connecting
        if self.state in (STATE_LAUNCHING, STATE_CONNECTING, STATE_RECONNECTING):
            self._sweep = min(self._sweep + 5, 270)
        elif self.state == STATE_CONNECTED:
            self._sweep = 270
        else:
            self._sweep = max(self._sweep - 4, 0)

        # Smooth glow alpha
        self._glow_alpha += (self._glow_target - self._glow_alpha) * 0.08

        # Shake decay
        if abs(self._shake_x) > 0.3:
            self._shake_x *= self._shake_decay
        else:
            self._shake_x = 0

        # Update ripple rings
        new_ripples = []
        for r in self._ripple_rings:
            r["r"] += r["speed"]
            r["alpha"] -= 0.012
            if r["alpha"] > 0.01:
                new_ripples.append(r)
        self._ripple_rings = new_ripples

        # Auto-spawn ripples when connecting
        if self.state in (STATE_LAUNCHING, STATE_CONNECTING, STATE_RECONNECTING):
            self._ripple_next -= 1
            if self._ripple_next <= 0:
                self._spawn_ripple(COLORS["connecting"])
                self._ripple_next = random.randint(15, 30)

        # Update particles
        for p in self._particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            if p["y"] < -10:
                p["y"] = self.size + 10
                p["x"] = random.uniform(0, self.size)
            if p["x"] < -10:
                p["x"] = self.size + 10
            elif p["x"] > self.size + 10:
                p["x"] = -10

        self.draw()
        self._anim_id = self.after(33, self._tick)  # ~30fps

    def draw(self):
        self.delete("all")
        cx = self.cx + self._shake_x
        cy = self.cy

        # Breathing scale
        breath = 1.0 + 0.015 * math.sin(self._breath_phase)
        r = int(self.base_r * breath)

        # ── Ambient particles (behind everything) ──
        for p in self._particles:
            a = int(p["alpha"] * 255)
            r_val = int(p["color"][1:3], 16)
            g_val = int(p["color"][3:5], 16)
            b_val = int(p["color"][5:7], 16)
            # tkinter doesn't support alpha, so we dim the color
            dim_r = int(r_val * p["alpha"])
            dim_g = int(g_val * p["alpha"])
            dim_b = int(b_val * p["alpha"])
            dim = f"#{dim_r:02x}{dim_g:02x}{dim_b:02x}"
            self.create_oval(p["x"]-p["r"], p["y"]-p["r"],
                           p["x"]+p["r"], p["y"]+p["r"],
                           fill=dim, outline="")

        # ── Ripple rings ──
        for rr in self._ripple_rings:
            a = int(rr["alpha"] * 255)
            r_val = int(rr["color"][1:3], 16)
            g_val = int(rr["color"][3:5], 16)
            b_val = int(rr["color"][5:7], 16)
            dim_r = int(r_val * rr["alpha"])
            dim_g = int(g_val * rr["alpha"])
            dim_b = int(b_val * rr["alpha"])
            dim = f"#{min(dim_r,255):02x}{min(dim_g,255):02x}{min(dim_b,255):02x}"
            self.create_oval(cx - rr["r"], cy - rr["r"],
                           cx + rr["r"], cy + rr["r"],
                           outline=dim, width=2)

        # ── Glow halo (multi-layer, alpha-based brightness) ──
        glow_colors = {
            STATE_CONNECTED: COLORS["success"],
            STATE_LAUNCHING: COLORS["connecting"],
            STATE_CONNECTING: COLORS["connecting"],
            STATE_RECONNECTING: COLORS["connecting"],
            STATE_ERROR: COLORS["danger"],
        }
        gc = glow_colors.get(self.state, "#333333")
        ga = self._glow_alpha

        for i in range(5, 0, -1):
            gr = r + i * 7
            # Mix glow color toward background based on distance + alpha
            brightness = ga * (1.0 - i * 0.18)
            brightness = max(0, min(1, brightness))
            r_val = int(int(gc[1:3], 16) * brightness)
            g_val = int(int(gc[3:5], 16) * brightness)
            b_val = int(int(gc[5:7], 16) * brightness)
            ring = f"#{r_val:02x}{g_val:02x}{b_val:02x}"
            self.create_oval(cx - gr, cy - gr, cx + gr, cy + gr,
                           outline=ring, width=2)

        # ── Orbital ring ──
        self.create_oval(cx - r, cy - r, cx + r, cy + r,
                        outline="#222222", width=2)

        # ── Rotating dots on ring ──
        rad = math.radians(self._angle)
        dot1_x = cx + r * math.cos(rad)
        dot1_y = cy + r * math.sin(rad)
        self.create_oval(dot1_x-3, dot1_y-3, dot1_x+3, dot1_y+3,
                        fill=COLORS["accent"], outline="")

        rad2 = math.radians(self._angle + 180)
        dot2_x = cx + r * math.cos(rad2)
        dot2_y = cy + r * math.sin(rad2)
        self.create_oval(dot2_x-2, dot2_y-2, dot2_x+2, dot2_y+2,
                        fill=COLORS["accent2"], outline="")

        # ── Inner circle ──
        inner_r = r - 22
        self.create_oval(cx - inner_r, cy - inner_r,
                        cx + inner_r, cy + inner_r,
                        fill=COLORS["portal"], outline="#282828", width=2)

        # ── Center icon ──
        if self.state == STATE_IDLE:
            # Power icon
            pr = 20
            self.create_arc(cx-pr, cy-pr, cx+pr, cy+pr,
                          start=30, extent=300,
                          outline=COLORS["text_muted"], width=3, style="arc")
            self.create_line(cx, cy-pr-2, cx, cy-pr+12,
                           fill=COLORS["text_muted"], width=3)

        elif self.state in (STATE_LAUNCHING, STATE_CONNECTING, STATE_RECONNECTING):
            # Spinning arc
            sa = self._sweep
            self.create_arc(cx-22, cy-22, cx+22, cy+22,
                          start=int(self._angle), extent=int(sa),
                          outline=COLORS["accent"], width=4, style="arc")

        elif self.state == STATE_CONNECTED:
            # Checkmark
            self.create_line(cx-14, cy+2, cx-4, cy+12,
                           fill=COLORS["success"], width=4, capstyle="round")
            self.create_line(cx-4, cy+12, cx+16, cy-10,
                           fill=COLORS["success"], width=4, capstyle="round")

        elif self.state == STATE_ERROR:
            # X mark
            self.create_line(cx-10, cy-10, cx+10, cy+10,
                           fill=COLORS["danger"], width=4, capstyle="round")
            self.create_line(cx+10, cy-10, cx-10, cy+10,
                           fill=COLORS["danger"], width=4, capstyle="round")


# ══════════════════════════════════════════════════════════
# Animated Background Particles
# ══════════════════════════════════════════════════════════
class ParticleBackground(ctk.CTkCanvas):
    """Floating ambient particles behind the main content."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, highlightthickness=0, bg=COLORS["bg"], **kwargs)
        self._particles = []
        self._anim_id = None

    def start(self):
        # Generate particles after the canvas is sized
        self.after(100, self._init_particles)

    def stop(self):
        if self._anim_id:
            self.after_cancel(self._anim_id)
            self._anim_id = None

    def _init_particles(self):
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 10 or h < 10:
            self.after(100, self._init_particles)
            return
        self._particles = []
        for _ in range(20):
            self._particles.append({
                "x": random.uniform(0, w),
                "y": random.uniform(0, h),
                "vx": random.uniform(-0.2, 0.2),
                "vy": random.uniform(-0.3, -0.05),
                "r": random.uniform(1, 2.5),
                "alpha": random.uniform(0.05, 0.2),
                "color": random.choice(["#f2711c", "#2dd4bf", "#a3a3a3", "#f2f2f2"]),
            })
        self._tick()

    def _tick(self):
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 10:
            self._anim_id = self.after(50, self._tick)
            return

        self.delete("all")
        for p in self._particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            if p["y"] < -10:
                p["y"] = h + 10
                p["x"] = random.uniform(0, w)
            if p["x"] < -10:
                p["x"] = w + 10
            elif p["x"] > w + 10:
                p["x"] = -10

            r_val = int(int(p["color"][1:3], 16) * p["alpha"])
            g_val = int(int(p["color"][3:5], 16) * p["alpha"])
            b_val = int(int(p["color"][5:7], 16) * p["alpha"])
            dim = f"#{r_val:02x}{g_val:02x}{b_val:02x}"
            self.create_oval(p["x"]-p["r"], p["y"]-p["r"],
                           p["x"]+p["r"], p["y"]+p["r"],
                           fill=dim, outline="")

        self._anim_id = self.after(50, self._tick)


# ══════════════════════════════════════════════════════════
# Main GUI
# ══════════════════════════════════════════════════════════
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
        self._pulse_id = None

        self._build_ui()
        self._animate_entry()
        self.portal.start()
        self.particles.start()

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
        ctk.CTkLabel(self.sidebar, text="Nikan.Developer\nNikanDeveloper56.github.io",
                      font=("Segoe UI", 10), text_color=COLORS["text_muted"]).pack(side="bottom", pady=12)

        # Main content
        self.main = ctk.CTkFrame(self, corner_radius=0, fg_color=COLORS["bg"])
        self.main.pack(side="right", fill="both", expand=True)

        # Particle background (fills main area)
        self.particles = ParticleBackground(self.main)
        self.particles.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.pages = {}
        self._build_home()
        self._build_logs()
        self._build_settings()
        self._build_about()
        self._switch_page("Home")

    def _build_home(self):
        page = ctk.CTkFrame(self.main, fg_color="transparent")
        self.pages["Home"] = page

        # Center container
        center = ctk.CTkFrame(page, fg_color="transparent")
        center.pack(expand=True, fill="both")

        # ── Hero portal area ──
        hero = ctk.CTkFrame(center, fg_color="transparent", height=200)
        hero.pack(fill="x", padx=32, pady=(32, 0))
        hero.pack_propagate(False)

        self.portal = ConnectPortal(hero, size=160, on_click=self._on_connect_click)
        self.portal.pack(expand=True)

        # ── Status labels (with smooth transitions) ──
        self.status_label = ctk.CTkLabel(center, text="Disconnected",
                                          font=("Segoe UI", 26, "bold"),
                                          text_color=COLORS["danger"])
        self.status_label.pack(pady=(8, 2))

        self.timer_label = ctk.CTkLabel(center, text="00:00:00",
                                         font=("Consolas", 20),
                                         text_color=COLORS["text_muted"])
        self.timer_label.pack()

        self.conn_info = ctk.CTkLabel(center, text="", font=("Segoe UI", 12),
                                       text_color=COLORS["text_muted"])
        self.conn_info.pack(pady=(2, 0))

        # ── Connect button ──
        self.connect_btn = ctk.CTkButton(center, text="⚡  Connect", height=48, corner_radius=12,
                                          font=("Segoe UI", 15, "bold"),
                                          fg_color=COLORS["accent"], hover_color="#e06a10",
                                          text_color="#0d0d0f",
                                          command=self._on_connect_click)
        self.connect_btn.pack(fill="x", padx=32, pady=(16, 6))

        self.reconnect_btn = ctk.CTkButton(center, text="🔀  Quick Reconnect", height=36, corner_radius=10,
                                            font=("Segoe UI", 12),
                                            fg_color=COLORS["surface2"], hover_color=COLORS["surface3"],
                                            text_color=COLORS["text"],
                                            command=self._quick_reconnect)
        self.reconnect_btn.pack(fill="x", padx=32, pady=(0, 8))

        # ── Options row ──
        opts = ctk.CTkFrame(center, fg_color=COLORS["surface"], corner_radius=10)
        opts.pack(fill="x", padx=32, pady=(0, 6))

        ctk.CTkLabel(opts, text="Protocol:", font=("Segoe UI", 11),
                      text_color=COLORS["text_muted"]).pack(side="left", padx=(12, 6), pady=10)
        self.protocol_var = ctk.StringVar(value="MASQUE (HTTP/3)")
        self.protocol_menu = ctk.CTkOptionMenu(opts, variable=self.protocol_var, values=PROTOCOLS,
                           command=self._on_protocol_change,
                           width=160, corner_radius=8, fg_color=COLORS["surface2"])
        self.protocol_menu.pack(side="left", pady=10)

        ctk.CTkLabel(opts, text="Scan:", font=("Segoe UI", 11),
                      text_color=COLORS["text_muted"]).pack(side="left", padx=(16, 6), pady=10)
        self.scan_var = ctk.StringVar(value="Balanced")
        self.scan_menu = ctk.CTkOptionMenu(opts, variable=self.scan_var, values=SCAN_MODES,
                           width=120, corner_radius=8, fg_color=COLORS["surface2"])
        self.scan_menu.pack(side="left", pady=10)

        # ── Stats row ──
        stats = ctk.CTkFrame(center, fg_color="transparent")
        stats.pack(fill="x", padx=32, pady=(0, 12))
        self.stat_protocol = self._stat_box(stats, "Protocol", "MASQUE")
        self.stat_port = self._stat_box(stats, "Port", "1819")
        self.stat_ip = self._stat_box(stats, "IP", "—")

    def _stat_box(self, parent, title, value):
        f = ctk.CTkFrame(parent, fg_color=COLORS["surface"], corner_radius=10, height=65)
        f.pack(side="left", fill="both", expand=True, padx=(0, 6))
        f.pack_propagate(False)
        ctk.CTkLabel(f, text=title, font=("Segoe UI", 10), text_color=COLORS["text_muted"]).pack(pady=(8, 1))
        lbl = ctk.CTkLabel(f, text=value, font=("Segoe UI", 14, "bold"), text_color=COLORS["text"])
        lbl.pack()
        return lbl

    def _build_logs(self):
        page = ctk.CTkFrame(self.main, fg_color="transparent")
        self.pages["Logs"] = page
        ctk.CTkLabel(page, text="Logs", font=("Segoe UI", 20, "bold"),
                      text_color=COLORS["text"], anchor="w").pack(fill="x", padx=32, pady=(24, 8))
        self.log_text = ctk.CTkTextbox(page, font=("Consolas", 11), fg_color=COLORS["surface"],
                                        text_color=COLORS["text_muted"], corner_radius=10,
                                        border_width=1, border_color=COLORS["border"])
        self.log_text.pack(fill="both", expand=True, padx=32, pady=(0, 12))
        self.log_text.configure(state="disabled")
        ctk.CTkButton(page, text="🗑  Clear Logs", height=32, corner_radius=8,
                       fg_color=COLORS["surface2"], hover_color=COLORS["surface3"],
                       text_color=COLORS["text"], command=self._clear_logs).pack(padx=32, pady=(0, 12))

    def _build_settings(self):
        page = ctk.CTkFrame(self.main, fg_color="transparent")
        self.pages["Settings"] = page
        ctk.CTkLabel(page, text="Settings", font=("Segoe UI", 20, "bold"),
                      text_color=COLORS["text"], anchor="w").pack(fill="x", padx=32, pady=(24, 8))

        row = ctk.CTkFrame(page, fg_color=COLORS["surface"], corner_radius=10)
        row.pack(fill="x", padx=32, pady=3)
        ctk.CTkLabel(row, text="SOCKS5 Port", font=("Segoe UI", 12),
                      text_color=COLORS["text"]).pack(side="left", padx=14, pady=10)
        self.port_entry = ctk.CTkEntry(row, width=90, corner_radius=8, fg_color=COLORS["surface2"],
                                        border_color=COLORS["border"], text_color=COLORS["text"])
        self.port_entry.insert(0, "1819")
        self.port_entry.pack(side="right", padx=14, pady=10)

        self.reconnect_row = ctk.CTkFrame(page, fg_color=COLORS["surface"], corner_radius=10)
        self.reconnect_row.pack(fill="x", padx=32, pady=3)
        ctk.CTkLabel(self.reconnect_row, text="Quick Reconnect", font=("Segoe UI", 12),
                      text_color=COLORS["text"]).pack(side="left", padx=14, pady=10)
        self.reconnect_toggle = ctk.CTkSwitch(self.reconnect_row, text="", onvalue=True, offvalue=False)
        self.reconnect_toggle.pack(side="right", padx=14, pady=10)
        self.reconnect_toggle.select()

        self.fragment_row = ctk.CTkFrame(page, fg_color=COLORS["surface"], corner_radius=10)
        self.fragment_row.pack(fill="x", padx=32, pady=3)
        self.fragment_row.pack_forget()
        ctk.CTkLabel(self.fragment_row, text="TLS Fragmentation (HTTP/2)", font=("Segoe UI", 12),
                      text_color=COLORS["text"]).pack(side="left", padx=14, pady=10)
        self.tls_toggle = ctk.CTkSwitch(self.fragment_row, text="", onvalue=True, offvalue=False)
        self.tls_toggle.pack(side="right", padx=14, pady=10)

        row4 = ctk.CTkFrame(page, fg_color=COLORS["surface"], corner_radius=10)
        row4.pack(fill="x", padx=32, pady=3)
        ctk.CTkLabel(row4, text="DNS Servers", font=("Segoe UI", 12),
                      text_color=COLORS["text"]).pack(side="left", padx=14, pady=10)
        self.dns_entry = ctk.CTkEntry(row4, width=180, corner_radius=8, fg_color=COLORS["surface2"],
                                       border_color=COLORS["border"], text_color=COLORS["text"])
        self.dns_entry.insert(0, "1.1.1.1, 1.0.0.1")
        self.dns_entry.pack(side="right", padx=14, pady=10)

        row5 = ctk.CTkFrame(page, fg_color=COLORS["surface"], corner_radius=10)
        row5.pack(fill="x", padx=32, pady=3)
        ctk.CTkLabel(row5, text="IP Version", font=("Segoe UI", 12),
                      text_color=COLORS["text"]).pack(side="left", padx=14, pady=10)
        self.ip_var = ctk.StringVar(value="Dual")
        ctk.CTkOptionMenu(row5, variable=self.ip_var, values=["IPv4", "IPv6", "Dual"],
                           width=90, corner_radius=8, fg_color=COLORS["surface2"]).pack(side="right", padx=14, pady=10)

        row6 = ctk.CTkFrame(page, fg_color=COLORS["surface"], corner_radius=10)
        row6.pack(fill="x", padx=32, pady=3)
        ctk.CTkLabel(row6, text="Noize Profile", font=("Segoe UI", 12),
                      text_color=COLORS["text"]).pack(side="left", padx=14, pady=10)
        self.noize_var = ctk.StringVar(value="Disabled")
        ctk.CTkOptionMenu(row6, variable=self.noize_var,
                           values=["Disabled", "Light", "Balanced", "Aggressive"],
                           width=110, corner_radius=8, fg_color=COLORS["surface2"]).pack(side="right", padx=14, pady=10)

        ctk.CTkButton(page, text="💾  Save Settings", height=38, corner_radius=10,
                       fg_color=COLORS["accent"], hover_color="#e06a10",
                       text_color="#0d0d0f", command=self._save_settings).pack(padx=32, pady=16)

    def _build_about(self):
        page = ctk.CTkFrame(self.main, fg_color="transparent")
        self.pages["About"] = page
        ctk.CTkLabel(page, text="About", font=("Segoe UI", 20, "bold"),
                      text_color=COLORS["text"], anchor="w").pack(fill="x", padx=32, pady=(24, 8))
        card = ctk.CTkFrame(page, fg_color=COLORS["surface"], corner_radius=14, height=260)
        card.pack(fill="x", padx=32, pady=8)
        card.pack_propagate(False)
        ctk.CTkLabel(card, text="AETHER", font=("Segoe UI", 34, "bold"),
                      text_color=COLORS["accent"]).pack(pady=(24, 2))
        ctk.CTkLabel(card, text=f"Version {VERSION}", font=("Segoe UI", 12),
                      text_color=COLORS["text_muted"]).pack()
        ctk.CTkLabel(card, text="Censorship Circumvention Client",
                      font=("Segoe UI", 13), text_color=COLORS["text"]).pack(pady=(4, 14))
        ctk.CTkFrame(card, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=28)
        ctk.CTkLabel(card, text="GUI built by Nikan (Nikan.Developer)",
                      font=("Segoe UI", 12, "bold"), text_color=COLORS["accent2"]).pack(pady=(14, 3))
        ctk.CTkLabel(card, text="NikanDeveloper56.github.io", font=("Segoe UI", 11),
                      text_color=COLORS["text_muted"]).pack()
        ctk.CTkLabel(page, text="This software is provided as-is. Use responsibly.",
                      font=("Segoe UI", 10), text_color=COLORS["text_muted"]).pack(side="bottom", pady=10)

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

    # ── Pulse animation on connect button ───────────────
    def _start_pulse(self):
        self._animate_pulse()

    def _animate_pulse(self):
        if self._pulse_id:
            self.after_cancel(self._pulse_id)

        if self._conn_state in (STATE_LAUNCHING, STATE_CONNECTING, STATE_RECONNECTING):
            # Smooth pulse between amber shades
            phase = time.time() * 3
            t = (math.sin(phase) + 1) / 2
            r = int(0xf2 + (0xf9 - 0xf2) * t)
            g = int(0x71 + (0x73 - 0x71) * t)
            b = int(0x1c + (0x16 - 0x1c) * t)
            self.connect_btn.configure(fg_color=f"#{r:02x}{g:02x}{b:02x}")
        elif self._conn_state == STATE_CONNECTED:
            self.connect_btn.configure(fg_color=COLORS["danger"])
        else:
            self.connect_btn.configure(fg_color=COLORS["accent"])

        self._pulse_id = self.after(60, self._animate_pulse)

    # ── State Machine ───────────────────────────────────
    def _set_state(self, new_state, info=""):
        old = self._conn_state
        self._conn_state = new_state
        self.portal.set_state(new_state)

        is_busy = new_state in (STATE_LAUNCHING, STATE_CONNECTING, STATE_RECONNECTING, STATE_DISCONNECTING)
        self.protocol_menu.configure(state="disabled" if is_busy else "normal")
        self.scan_menu.configure(state="disabled" if is_busy else "normal")

        if new_state == STATE_IDLE:
            self.status_label.configure(text="Disconnected", text_color=COLORS["danger"])
            self.connect_btn.configure(text="⚡  Connect", fg_color=COLORS["accent"], hover_color="#e06a10")
            self.conn_info.configure(text="")
            self.stat_ip.configure(text="—")
            self._stop_timer()

        elif new_state == STATE_LAUNCHING:
            self.status_label.configure(text="Starting…", text_color=COLORS["warning"])
            self.connect_btn.configure(text="⏹  Cancel", fg_color=COLORS["warning"], hover_color="#dc2626")
            self.conn_info.configure(text="Launching Aether engine…")

        elif new_state == STATE_CONNECTING:
            self.status_label.configure(text="Connecting…", text_color=COLORS["warning"])
            self.connect_btn.configure(text="⏹  Cancel", fg_color=COLORS["warning"], hover_color="#dc2626")
            self.conn_info.configure(text=f"Scanning routes ({self.scan_var.get()})…")

        elif new_state == STATE_CONNECTED:
            self.status_label.configure(text="Connected", text_color=COLORS["success"])
            self.connect_btn.configure(text="⏹  Disconnect", fg_color=COLORS["danger"], hover_color="#dc2626")
            self.conn_info.configure(text=f"SOCKS5 → 127.0.0.1:{self.port_entry.get().strip()}")
            proto = self.protocol_var.get()
            if "MASQUE" in proto:
                short = "MASQUE" if "HTTP/3" in proto else "MASQUE/H2"
            elif "WireGuard" in proto:
                short = "WireGuard"
            else:
                short = "WARP-in-WARP"
            self.stat_protocol.configure(text=short)
            self.stat_port.configure(text=self.port_entry.get().strip())
            self._start_timer()
            threading.Thread(target=self._fetch_tunnel_ip, daemon=True).start()

        elif new_state == STATE_RECONNECTING:
            attempt = info
            self.status_label.configure(text=f"Reconnecting… ({attempt}/{MAX_AUTO_RETRIES})",
                                          text_color=COLORS["warning"])

        elif new_state == STATE_DISCONNECTING:
            self.status_label.configure(text="Disconnecting…", text_color=COLORS["warning"])
            self.connect_btn.configure(text="⏹  Disconnect", fg_color=COLORS["danger"], hover_color="#dc2626")

        elif new_state == STATE_ERROR:
            self.status_label.configure(text=info or "Error", text_color=COLORS["danger"])
            self.connect_btn.configure(text="⚡  Connect", fg_color=COLORS["accent"], hover_color="#e06a10")
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

    def _on_protocol_change(self, choice):
        is_http2 = "HTTP/2" in choice
        if is_http2:
            self.fragment_row.pack(fill="x", padx=32, pady=3, after=self.reconnect_row)
        else:
            self.fragment_row.pack_forget()
            self.tls_toggle.deselect()

    def _build_cmd(self, binary):
        proto = self.protocol_var.get()
        scan = self.scan_var.get().lower()
        port = self.port_entry.get().strip()
        cmd = [binary, "--bind", f"127.0.0.1:{port}", "--scan", scan]

        if "WireGuard" in proto:
            cmd.append("--wg")
        elif "WARP-in-WARP" in proto:
            cmd.append("--gool")
        else:
            cmd.append("--masque")
            if "HTTP/2" in proto:
                cmd.append("--h2")

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

        if port_is_live("127.0.0.1", port):
            self._log(f"Port {port} already in use. Is another instance running?")
            self._set_state(STATE_ERROR, f"Port {port} in use")
            return

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

        threading.Thread(target=self._read_logs, daemon=True).start()
        self.monitor_thread = threading.Thread(
            target=self._monitor_connect, args=(cmd, port), daemon=True
        )
        self.monitor_thread.start()

    def _read_logs(self):
        try:
            for line in self.process.stdout:
                self._log(line.rstrip())
        except Exception:
            pass

    def _monitor_connect(self, cmd, port):
        scan = self.scan_var.get().lower()
        timeout = CONNECT_TIMEOUTS.get(scan, 150)
        deadline = time.time() + timeout
        announced_connecting = False

        while True:
            time.sleep(0.4)
            if self.user_requested_stop:
                return

            if self.process and self.process.poll() is not None:
                rc = self.process.returncode
                self._log(f"Process exited with code {rc}")
                self._handle_failure(cmd, port, f"Process exited (code {rc})")
                return

            if not announced_connecting and time.time() > deadline - timeout + 3:
                self.after(0, lambda: self._set_state(STATE_CONNECTING))
                announced_connecting = True

            if port_is_live("127.0.0.1", port):
                self._log(f"SOCKS5 port {port} is live — connected!")
                self.after(0, lambda: self._set_state(STATE_CONNECTED))
                self.retry_count = 0
                self._monitor_connected(cmd, port)
                return

            if time.time() >= deadline:
                self._log(f"Timeout after {timeout}s waiting for route")
                if self.process:
                    try:
                        self.process.terminate()
                    except Exception:
                        pass
                self._handle_failure(cmd, port, f"Timeout ({timeout}s)")
                return

    def _fetch_tunnel_ip(self):
        port = self.port_entry.get().strip()
        ip = None
        for attempt in range(3):
            if self.user_requested_stop or self._conn_state != STATE_CONNECTED:
                return
            try:
                ip = self._socks5_ip_get(port)
                if ip:
                    break
            except Exception as e:
                self._log(f"IP check attempt {attempt+1} failed: {e}")
                time.sleep(2)
        if ip:
            self._log(f"Tunnel public IP: {ip}")
            self.after(0, lambda: self.stat_ip.configure(text=ip))
        else:
            self._log("Could not determine tunnel public IP")

    def _socks5_ip_get(self, port, timeout=10):
        host = "api.ipify.org"
        host_bytes = host.encode()
        port_bytes = struct.pack(">H", 80)

        sock = socket.create_connection(("127.0.0.1", int(port)), timeout=timeout)
        sock.settimeout(timeout)
        try:
            sock.sendall(b"\x05\x01\x00")
            resp = sock.recv(2)
            if resp != b"\x05\x00":
                raise Exception(f"SOCKS5 handshake failed: {resp.hex()}")

            req = b"\x05\x01\x00\x03" + bytes([len(host_bytes)]) + host_bytes + port_bytes
            sock.sendall(req)
            resp = sock.recv(10)
            if len(resp) < 2 or resp[1] != 0:
                raise Exception(f"SOCKS5 CONNECT failed: {resp.hex()}")

            sock.sendall(b"GET / HTTP/1.1\r\nHost: api.ipify.org\r\nConnection: close\r\n\r\n")
            data = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                data += chunk
                if len(data) > 65536:
                    break

            text = data.decode(errors="replace")
            if "\r\n\r\n" in text:
                body = text.split("\r\n\r\n", 1)[1]
                return body.strip() or None
            return None
        finally:
            sock.close()

    def _monitor_connected(self, cmd, port):
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

        def wait_exit():
            start = time.time()
            while time.time() - start < 3:
                if self.process and self.process.poll() is not None:
                    break
                time.sleep(0.2)
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
        self._log("Settings saved.")

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
        self.portal.stop()
        self.particles.stop()
        if self._pulse_id:
            self.after_cancel(self._pulse_id)
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
