"""QuickFind ikonu oluşturma scripti — modern gradient şimşek ikonu"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os, math

def create_icon():
    sizes = [256]
    images = []

    for size in sizes:
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # ─── Background: rounded square with gradient ───
        margin = int(size * 0.06)
        radius = int(size * 0.22)

        # Gradient background
        for y in range(size):
            t = y / size
            r = int(88 * (1 - t) + 15 * t)
            g = int(40 * (1 - t) + 20 * t)
            b = int(220 * (1 - t) + 180 * t)
            for x in range(size):
                # Check if inside rounded rect
                in_rect = True
                cx, cy = x, y
                if cx < margin + radius and cy < margin + radius:
                    if (cx - margin - radius)**2 + (cy - margin - radius)**2 > radius**2:
                        in_rect = False
                elif cx > size - margin - radius - 1 and cy < margin + radius:
                    if (cx - size + margin + radius + 1)**2 + (cy - margin - radius)**2 > radius**2:
                        in_rect = False
                elif cx < margin + radius and cy > size - margin - radius - 1:
                    if (cx - margin - radius)**2 + (cy - size + margin + radius + 1)**2 > radius**2:
                        in_rect = False
                elif cx > size - margin - radius - 1 and cy > size - margin - radius - 1:
                    if (cx - size + margin + radius + 1)**2 + (cy - size + margin + radius + 1)**2 > radius**2:
                        in_rect = False
                elif cx < margin or cx >= size - margin or cy < margin or cy >= size - margin:
                    in_rect = False

                if in_rect:
                    img.putpixel((x, y), (r, g, b, 240))

        # ─── Glass overlay (top half lighter) ───
        overlay = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        odraw = ImageDraw.Draw(overlay)
        for y in range(size // 2):
            t = y / (size // 2)
            alpha = int(60 * (1 - t))
            for x in range(size):
                px = img.getpixel((x, y))
                if px[3] > 0:
                    overlay.putpixel((x, y), (255, 255, 255, alpha))
        img = Image.alpha_composite(img, overlay)

        draw = ImageDraw.Draw(img)

        # ─── Lightning bolt ───
        cx, cy = size // 2, size // 2
        s = size / 256  # scale factor

        bolt_points = [
            (cx + 10*s, cy - 80*s),
            (cx - 15*s, cy - 10*s),
            (cx + 12*s, cy - 10*s),
            (cx - 10*s, cy + 80*s),
            (cx + 18*s, cy + 8*s),
            (cx - 10*s, cy + 8*s),
        ]

        # Glow effect
        glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        gdraw = ImageDraw.Draw(glow)
        gdraw.polygon(bolt_points, fill=(255, 255, 180, 100))
        glow = glow.filter(ImageFilter.GaussianBlur(radius=12*s))
        img = Image.alpha_composite(img, glow)

        draw = ImageDraw.Draw(img)
        # Main bolt
        draw.polygon(bolt_points, fill=(255, 255, 255, 245))

        # Inner highlight
        inner_points = [
            (cx + 8*s, cy - 65*s),
            (cx - 8*s, cy - 10*s),
            (cx + 8*s, cy - 10*s),
            (cx - 4*s, cy + 60*s),
            (cx + 12*s, cy + 8*s),
            (cx - 4*s, cy + 8*s),
        ]
        draw.polygon(inner_points, fill=(255, 255, 255, 255))

        # ─── Subtle search circle (top-right) ───
        sc_x, sc_y = cx + 48*s, cy - 48*s
        sc_r = 22*s
        draw.ellipse(
            [sc_x - sc_r, sc_y - sc_r, sc_x + sc_r, sc_y + sc_r],
            outline=(255, 255, 255, 160), width=max(int(3*s), 2)
        )
        # Handle
        hx1 = sc_x + sc_r * 0.7
        hy1 = sc_y + sc_r * 0.7
        hx2 = hx1 + 12*s
        hy2 = hy1 + 12*s
        draw.line([(hx1, hy1), (hx2, hy2)], fill=(255, 255, 255, 160),
                  width=max(int(3*s), 2))

        images.append(img)

    # Save as .ico
    icon_path = os.path.join(os.path.dirname(__file__), "quickfind.ico")
    # Create multiple sizes for .ico
    ico_images = []
    base = images[0]
    for s in [16, 24, 32, 48, 64, 128, 256]:
        resized = base.resize((s, s), Image.LANCZOS)
        ico_images.append(resized)

    ico_images[-1].save(icon_path, format="ICO", sizes=[(s, s) for s in [16, 24, 32, 48, 64, 128, 256]],
                         append_images=ico_images[:-1])
    print(f"Icon saved: {icon_path}")

    # Also save PNG
    png_path = os.path.join(os.path.dirname(__file__), "quickfind.png")
    base.save(png_path)
    print(f"PNG saved: {png_path}")


if __name__ == "__main__":
    create_icon()
