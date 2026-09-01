#!/usr/bin/env python3
"""Generate Aether app icon — A-shaped triangle logo, similar to V2RayN style."""
from PIL import Image, ImageDraw, ImageFont
import os, math

SIZES = [16, 32, 48, 64, 128, 256, 512]

def draw_icon(size):
    """Draw the Aether 'A' triangle logo at given size."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2

    # Background rounded rect (dark navy)
    bg_pad = int(size * 0.02)
    bg_radius = int(size * 0.18)
    draw.rounded_rectangle(
        [bg_pad, bg_pad, size - bg_pad, size - bg_pad],
        radius=bg_radius,
        fill=(13, 17, 23, 255)  # #0d1117
    )

    # Outer triangle (blue) — forms the "A"
    tri_pad = int(size * 0.12)
    outer_top = (cx, tri_pad + int(size * 0.04))
    outer_bl = (tri_pad, size - tri_pad)
    outer_br = (size - tri_pad, size - tri_pad)

    # Glow effect — slightly larger, blurred
    glow_pad = int(size * 0.02)
    glow_top = (cx, outer_top[1] - glow_pad)
    glow_bl = (outer_bl[0] - glow_pad, outer_bl[1] + glow_pad)
    glow_br = (outer_br[0] + glow_pad, outer_br[1] + glow_pad)
    draw.polygon([glow_top, glow_bl, glow_br], fill=(88, 166, 255, 40))

    # Main outer triangle
    draw.polygon([outer_top, outer_bl, outer_br], fill=(88, 166, 255, 255))  # #58a6ff

    # Inner triangle cutout (darker) — creates the "A" shape with a hole
    in_top = (cx, outer_top[1] + int(size * 0.18))
    in_bl = (outer_bl[0] + int(size * 0.18), outer_bl[1] - int(size * 0.02))
    in_br = (outer_br[0] - int(size * 0.18), outer_br[1] - int(size * 0.02))
    draw.polygon([in_top, in_bl, in_br], fill=(13, 17, 23, 255))

    # Horizontal bar of the "A" (green/teal accent)
    bar_y = int(cy + size * 0.04)
    bar_h = int(size * 0.07)
    # Calculate bar width at this height (interpolate along triangle edges)
    t = (bar_y - outer_top[1]) / (outer_bl[1] - outer_top[1])
    bar_left = int(outer_top[0] + t * (outer_bl[0] - outer_top[0]))
    bar_right = int(outer_top[0] + t * (outer_br[0] - outer_top[0]))
    bar_inner_left = int(in_top[0] + t * (in_bl[0] - in_top[0]))
    bar_inner_right = int(in_top[0] + t * (in_br[0] - in_top[0]))

    bar_left = max(bar_left + int(size * 0.03), bar_left)
    bar_right = min(bar_right - int(size * 0.03), bar_right)

    draw.rectangle(
        [bar_left, bar_y, bar_right, bar_y + bar_h],
        fill=(63, 185, 80, 255)  # #3fb950 green
    )
    # Cut the inner triangle hole from the bar
    draw.rectangle(
        [bar_inner_left, bar_y, bar_inner_right, bar_y + bar_h],
        fill=(13, 17, 23, 255)
    )

    # Small accent glow at apex
    apex_glow_r = int(size * 0.04)
    for i in range(apex_glow_r, 0, -1):
        alpha = int(60 * (1 - i / apex_glow_r))
        draw.ellipse(
            [cx - i, outer_top[1] - i // 2, cx + i, outer_top[1] + i // 2],
            fill=(88, 166, 255, alpha)
        )

    return img


def main():
    out_dir = os.path.join(os.path.dirname(__file__), "..", "assets")
    os.makedirs(out_dir, exist_ok=True)

    # Generate PNGs
    for s in SIZES:
        icon = draw_icon(s)
        icon.save(os.path.join(out_dir, f"icon-{s}.png"))
        print(f"  icon-{s}.png")

    # Generate ICO with multiple sizes
    icons = [draw_icon(s) for s in [16, 32, 48, 64, 128, 256]]
    icons[0].save(
        os.path.join(out_dir, "icon.ico"),
        format="ICO",
        sizes=[(s, s) for s in [16, 32, 48, 64, 128, 256]],
        append_images=icons[1:]
    )
    print("  icon.ico")

    # Generate large PNG for README/docs (512x512)
    draw_icon(512).save(os.path.join(out_dir, "logo.png"))
    print("  logo.png (512x512)")

    print("Done!")


if __name__ == "__main__":
    main()
