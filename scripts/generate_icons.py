"""Generate favicon and PWA icons for AO Copilot."""

from PIL import Image, ImageDraw, ImageFont
import os

BRAND_COLOR = (37, 99, 235)  # #2563EB
WHITE = (255, 255, 255)
OUTPUT_DIR = os.path.join(
    os.path.dirname(__file__), "..", "apps", "web", "public", "icons"
)
FAVICON_SVG_PATH = os.path.join(
    os.path.dirname(__file__), "..", "apps", "web", "public", "favicon.svg"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)


def rounded_rectangle(draw, xy, radius, fill):
    """Draw a rounded rectangle."""
    x0, y0, x1, y1 = xy
    r = radius
    # Four corners as circles
    draw.ellipse([x0, y0, x0 + 2 * r, y0 + 2 * r], fill=fill)
    draw.ellipse([x1 - 2 * r, y0, x1, y0 + 2 * r], fill=fill)
    draw.ellipse([x0, y1 - 2 * r, x0 + 2 * r, y1], fill=fill)
    draw.ellipse([x1 - 2 * r, y1 - 2 * r, x1, y1], fill=fill)
    # Two rectangles to fill the rest
    draw.rectangle([x0 + r, y0, x1 - r, y1], fill=fill)
    draw.rectangle([x0, y0 + r, x1, y1 - r], fill=fill)


def create_icon(size, radius, font_size, output_path):
    """Create a PNG icon with rounded rect background and 'AO' text."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw rounded rectangle background
    rounded_rectangle(draw, (0, 0, size, size), radius, BRAND_COLOR)

    # Try to load a bold font, fall back to default
    font = None
    # Common bold font paths on Windows
    font_candidates = [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/calibrib.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for fp in font_candidates:
        if os.path.exists(fp):
            try:
                font = ImageFont.truetype(fp, font_size)
                break
            except Exception:
                continue

    if font is None:
        font = ImageFont.load_default()

    text = "AO"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    # Center the text
    x = (size - tw) / 2 - bbox[0]
    y = (size - th) / 2 - bbox[1]
    draw.text((x, y), text, fill=WHITE, font=font)

    img.save(output_path, "PNG")
    file_size = os.path.getsize(output_path)
    print(f"Created {output_path} ({size}x{size}, {file_size} bytes)")


def create_favicon_svg():
    """Create an SVG favicon with the same design."""
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <rect width="512" height="512" rx="80" ry="80" fill="#2563EB"/>
  <text x="256" y="295" font-family="Arial, Helvetica, sans-serif" font-weight="bold"
        font-size="220" fill="white" text-anchor="middle" dominant-baseline="central">AO</text>
</svg>"""
    with open(FAVICON_SVG_PATH, "w", encoding="utf-8") as f:
        f.write(svg)
    file_size = os.path.getsize(FAVICON_SVG_PATH)
    print(f"Created {FAVICON_SVG_PATH} ({file_size} bytes)")


if __name__ == "__main__":
    create_icon(512, 80, 220, os.path.join(OUTPUT_DIR, "icon-512.png"))
    create_icon(192, 30, 82, os.path.join(OUTPUT_DIR, "icon-192.png"))
    create_favicon_svg()
    print("Done!")
