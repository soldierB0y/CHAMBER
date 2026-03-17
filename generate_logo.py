"""
Genera el logo de Chamber: cilindro de revólver con cámaras hexagonales brillantes.
Ejecutar una vez para crear logo.png.
"""
import math
from PIL import Image, ImageDraw, ImageFilter, ImageFont

SIZE = 512
CENTER = SIZE // 2
BG_COLOR = (47, 48, 56)       # #2f3038
BODY_COLOR = (55, 60, 75)     # Cuerpo del cilindro
EDGE_CYAN = (0, 210, 255)     # Borde cyan brillante
GLOW_CYAN = (0, 180, 240, 180)
CHAMBER_LIT = (0, 160, 255)   # Cámara encendida
CHAMBER_DARK = (50, 55, 68)   # Cámara apagada
HUB_COLOR = (65, 70, 85)      # Centro


def draw_rounded_hexagon(draw, cx, cy, radius, fill, outline=None, outline_width=0):
    """Draw a hexagon at (cx, cy)."""
    points = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        px = cx + radius * math.cos(angle)
        py = cy + radius * math.sin(angle)
        points.append((px, py))
    draw.polygon(points, fill=fill, outline=outline, width=outline_width)


def make_logo():
    # Main image with alpha
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Glow layer
    glow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)

    # ── Cylinder body (scalloped circle) ──
    body_r = int(SIZE * 0.40)
    notch_count = 6
    notch_depth = int(SIZE * 0.04)
    chamber_orbit = int(SIZE * 0.22)

    # Draw scalloped outline
    # First draw the main circle
    points = []
    steps = 360
    for i in range(steps):
        angle = math.radians(i)
        r = body_r
        # Create notches between chambers
        for n in range(notch_count):
            notch_angle = math.radians(60 * n)
            diff = abs(((angle - notch_angle + math.pi) % (2 * math.pi)) - math.pi)
            if diff < math.radians(12):
                depth = notch_depth * (1 - diff / math.radians(12))
                r = body_r + depth
        px = CENTER + r * math.cos(angle)
        py = CENTER + r * math.sin(angle)
        points.append((px, py))

    # Draw body fill
    draw.polygon(points, fill=BODY_COLOR)
    # Draw cyan edge
    draw.polygon(points, outline=EDGE_CYAN, width=3)

    # Glow on edge
    glow_draw.polygon(points, outline=(*EDGE_CYAN, 100), width=8)

    # ── Center hub ──
    hub_r = int(SIZE * 0.07)
    draw.ellipse(
        [CENTER - hub_r, CENTER - hub_r, CENTER + hub_r, CENTER + hub_r],
        fill=HUB_COLOR, outline=(80, 85, 100), width=2
    )
    inner_r = int(SIZE * 0.035)
    draw.ellipse(
        [CENTER - inner_r, CENTER - inner_r, CENTER + inner_r, CENTER + inner_r],
        fill=(45, 48, 60), outline=(70, 75, 88), width=1
    )

    # ── Chambers (6 hexagons in a ring) ──
    lit_chambers = [True, True, True, True, False, False]  # 4 lit, 2 dark

    for i in range(6):
        angle = math.radians(60 * i - 90)  # Start from top
        cx = CENTER + chamber_orbit * math.cos(angle)
        cy = CENTER + chamber_orbit * math.sin(angle)
        hex_r = int(SIZE * 0.065)

        if lit_chambers[i]:
            # Glow behind lit chamber
            glow_r = int(hex_r * 2.2)
            glow_draw.ellipse(
                [cx - glow_r, cy - glow_r, cx + glow_r, cy + glow_r],
                fill=(0, 140, 220, 60)
            )
            # Lit chamber
            draw_rounded_hexagon(draw, cx, cy, hex_r, fill=CHAMBER_LIT,
                                 outline=(0, 220, 255), outline_width=2)
            # Inner bright spot
            inner = int(hex_r * 0.5)
            draw.ellipse(
                [cx - inner, cy - inner, cx + inner, cy + inner],
                fill=(100, 210, 255)
            )
        else:
            # Dark chamber
            draw_rounded_hexagon(draw, cx, cy, hex_r, fill=CHAMBER_DARK,
                                 outline=(75, 80, 95), outline_width=2)
            # Hollow center
            inner = int(hex_r * 0.45)
            draw_rounded_hexagon(draw, cx, cy, inner, fill=(40, 43, 55),
                                 outline=(60, 65, 78), outline_width=1)

    # Apply glow blur
    glow = glow.filter(ImageFilter.GaussianBlur(radius=12))

    # Composite: glow under main
    result = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    result = Image.alpha_composite(result, glow)
    result = Image.alpha_composite(result, img)

    return result


def main():
    import os
    logo = make_logo()
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
    logo.save(out_path, "PNG")
    print(f"Logo guardado en: {out_path}")

    # Also create an .ico for window icon
    ico_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.ico")
    icon_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    logo_rgb = Image.new("RGBA", (SIZE, SIZE), BG_COLOR)
    logo_rgb = Image.alpha_composite(logo_rgb, logo)
    logo_rgb.save(ico_path, format="ICO",
                  sizes=[(s, s) for s, _ in icon_sizes])
    print(f"Icono guardado en: {ico_path}")


BG_COLOR_TUPLE = BG_COLOR

if __name__ == "__main__":
    main()
