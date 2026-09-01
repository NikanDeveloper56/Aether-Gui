#!/usr/bin/env python3
"""Generate NikanDeveloper GitHub profile picture."""
from PIL import Image, ImageDraw, ImageFont
import math, os

SIZE = 1024
img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)
cx, cy = SIZE // 2, SIZE // 2

# Background circle (dark)
draw.ellipse([20, 20, SIZE-20, SIZE-20], fill=(13, 17, 23, 255))

# Outer glow ring
for i in range(8):
    alpha = int(30 * (1 - i/8))
    r = SIZE//2 - 30 + i
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=(88, 166, 255, alpha), width=2)

# Draw "N" using geometric triangles (N for Nikan)
# Left vertical bar of N
bar_w = int(SIZE * 0.12)
bar_h = int(SIZE * 0.55)
n_left = cx - int(SIZE * 0.22)
n_top = cy - bar_h // 2

# Left bar
draw.rounded_rectangle(
    [n_left, n_top, n_left + bar_w, n_top + bar_h],
    radius=int(SIZE * 0.02),
    fill=(88, 166, 255, 255)
)

# Right bar
n_right = cx + int(SIZE * 0.22) - bar_w
draw.rounded_rectangle(
    [n_right, n_top, n_right + bar_w, n_top + bar_h],
    radius=int(SIZE * 0.02),
    fill=(88, 166, 255, 255)
)

# Diagonal bar of N (connecting top-left to bottom-right)
diag_points = [
    (n_left + bar_w, n_top),                    # top-left inner
    (n_left + bar_w + int(SIZE*0.04), n_top),   # slight offset
    (n_right + bar_w, n_top + bar_h),            # bottom-right
    (n_right, n_top + bar_h),                     # bottom-right inner
]
draw.polygon(diag_points, fill=(63, 185, 80, 255))  # green accent

# Small triangle accent at top (like Aether logo)
tri_size = int(SIZE * 0.08)
tri_top = (cx, n_top - int(SIZE * 0.06))
tri_bl = (cx - tri_size, n_top + int(SIZE * 0.02))
tri_br = (cx + tri_size, n_top + int(SIZE * 0.02))
draw.polygon([tri_top, tri_bl, tri_br], fill=(88, 166, 255, 180))

# Bottom accent line
line_y = n_top + bar_h + int(SIZE * 0.06)
line_w = int(SIZE * 0.35)
draw.rounded_rectangle(
    [cx - line_w//2, line_y, cx + line_w//2, line_y + int(SIZE * 0.015)],
    radius=int(SIZE * 0.005),
    fill=(88, 166, 255, 120)
)

# Save
out = os.path.join(os.path.dirname(__file__), "..", "assets", "profile.png")
img.save(out, "PNG")
print(f"Saved: {out} ({SIZE}x{SIZE})")

# Also save a smaller version
img_small = img.resize((256, 256), Image.LANCZOS)
img_small.save(os.path.join(os.path.dirname(__file__), "..", "assets", "profile-256.png"), "PNG")
print("Saved: profile-256.png (256x256)")
