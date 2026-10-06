"""
Generates enterprise-grade, industrial standard SVG, PNG, and ICO logo & favicon assets.
"""
import os
import math
from PIL import Image, ImageDraw

def create_svg():
    return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" width="128" height="128">
  <defs>
    <!-- Background Gradient (Obsidian Titanium) -->
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0b0f19" />
      <stop offset="50%" stop-color="#111827" />
      <stop offset="100%" stop-color="#070a10" />
    </linearGradient>

    <!-- Metallic Rim Gradient -->
    <linearGradient id="rimGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#818cf8" />
      <stop offset="30%" stop-color="#38bdf8" />
      <stop offset="70%" stop-color="#c084fc" />
      <stop offset="100%" stop-color="#4f46e5" />
    </linearGradient>

    <!-- Stream A (Electric Indigo to Violet) -->
    <linearGradient id="streamA" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#a5b4fc" />
      <stop offset="40%" stop-color="#6366f1" />
      <stop offset="100%" stop-color="#4338ca" />
    </linearGradient>

    <!-- Stream B (Cyan Plasma to Azure) -->
    <linearGradient id="streamB" x1="100%" y1="100%" x2="0%" y2="0%">
      <stop offset="0%" stop-color="#67e8f9" />
      <stop offset="40%" stop-color="#06b6d4" />
      <stop offset="100%" stop-color="#0284c7" />
    </linearGradient>

    <!-- Prism Core Glow -->
    <radialGradient id="coreGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#ffffff" />
      <stop offset="35%" stop-color="#e0e7ff" />
      <stop offset="70%" stop-color="#38bdf8" />
      <stop offset="100%" stop-color="#6366f1" stop-opacity="0" />
    </radialGradient>

    <!-- Soft Filter for ambient glow -->
    <filter id="softGlow" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="3" result="blur" />
      <feMerge>
        <feMergeNode in="blur" />
        <feMergeNode in="SourceGraphic" />
      </feMerge>
    </filter>

    <filter id="sparkle" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="1.5" result="glow" />
      <feMerge>
        <feMergeNode in="glow" />
        <feMergeNode in="SourceGraphic" />
      </feMerge>
    </filter>
  </defs>

  <!-- Base Dark Squircle with Precision Metallic Rim -->
  <rect x="5" y="5" width="118" height="118" rx="26" fill="url(#bgGrad)" stroke="url(#rimGrad)" stroke-width="2.5" />

  <!-- Background Metric Coordinate Crosshairs -->
  <line x1="20" y1="64" x2="108" y2="64" stroke="#1f293d" stroke-width="1.2" stroke-dasharray="3,3" opacity="0.6" />
  <line x1="64" y1="20" x2="64" y2="108" stroke="#1f293d" stroke-width="1.2" stroke-dasharray="3,3" opacity="0.6" />
  <circle cx="64" cy="64" r="38" fill="none" stroke="#1f293d" stroke-width="1" stroke-dasharray="2,4" opacity="0.5" />

  <!-- Flow Conduit A (Upper Left Entity stream) -->
  <path d="M 28 36 C 44 36, 52 46, 64 64 C 54 54, 44 48, 28 48 Z" fill="url(#streamA)" opacity="0.95" />
  <path d="M 32 32 C 48 32, 58 48, 64 64 C 58 56, 48 42, 32 42 Z" fill="#c7d2fe" opacity="0.35" />

  <!-- Flow Conduit B (Lower Right Entity stream) -->
  <path d="M 100 92 C 84 92, 76 82, 64 64 C 74 74, 84 80, 100 80 Z" fill="url(#streamB)" opacity="0.95" />
  <path d="M 96 96 C 80 96, 70 80, 64 64 C 70 72, 80 86, 96 86 Z" fill="#a5f3fc" opacity="0.35" />

  <!-- Interlocking Precision Wings (Matching Engine Convergent Vector) -->
  <path d="M 34 50 C 46 50, 56 56, 72 64 C 60 66, 48 62, 34 50 Z" fill="url(#streamA)" filter="url(#softGlow)" />
  <path d="M 94 78 C 82 78, 72 72, 56 64 C 68 62, 80 66, 94 78 Z" fill="url(#streamB)" filter="url(#softGlow)" />

  <!-- Radiant Core (Match Resolution Point) -->
  <circle cx="64" cy="64" r="16" fill="url(#coreGlow)" filter="url(#softGlow)" />

  <!-- 4-Point Faceted Diamond Match Star -->
  <path d="M 64 45 L 68 60 L 83 64 L 68 68 L 64 83 L 60 68 L 45 64 L 60 60 Z" fill="#ffffff" filter="url(#sparkle)" />
  <circle cx="64" cy="64" r="3.5" fill="#38bdf8" />

  <!-- Precision Calibration Pips -->
  <circle cx="30" cy="42" r="3.5" fill="#818cf8" />
  <circle cx="98" cy="86" r="3.5" fill="#22d3ee" />
</svg>'''

def generate_png_and_ico(output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    # Render high-resolution PNG using PIL
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Base Squircle / Rounded Rect
    margin = 10
    corner_r = 56
    # Gradient background simulated via concentric rounded rects
    for i in range(margin, margin + 4):
        # Rim stroke gradient
        draw.rounded_rectangle(
            [margin - (4 - i), margin - (4 - i), size - margin + (4 - i), size - margin + (4 - i)],
            radius=corner_r + (4 - i),
            outline=(99, 102, 241, 220),
            width=2
        )

    # Fill base
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=corner_r,
        fill=(11, 15, 25, 255),
        outline=(56, 189, 248, 255),
        width=4
    )

    # Grid lines
    center = size // 2
    for offset in range(-50, 51, 25):
        if offset != 0:
            draw.line([(center + offset, center - 60), (center + offset, center + 60)], fill=(30, 41, 59, 140), width=1)
            draw.line([(center - 60, center + offset), (center + 60, center + offset)], fill=(30, 41, 59, 140), width=1)

    # 2. Draw Convergence Stream A (Indigo Wing)
    points_a = [
        (56, 72), (76, 72), (128, 128), (148, 128), (112, 96), (76, 88)
    ]
    draw.polygon([(p[0], p[1]) for p in points_a], fill=(99, 102, 241, 230))
    # Stream curve A
    draw.chord([48, 48, 160, 160], start=180, end=315, fill=(79, 70, 229, 220))

    # 3. Draw Convergence Stream B (Cyan Wing)
    points_b = [
        (size - 56, size - 72), (size - 76, size - 72), (128, 128), (108, 128), (size - 112, size - 96), (size - 76, size - 88)
    ]
    draw.polygon([(p[0], p[1]) for p in points_b], fill=(6, 182, 212, 230))
    draw.chord([size - 160, size - 160, size - 48, size - 48], start=0, end=135, fill=(14, 165, 233, 220))

    # 4. Central Diamond Star
    diamond_r = 32
    diamond_thin = 10
    poly = [
        (center, center - diamond_r),
        (center + diamond_thin, center - diamond_thin),
        (center + diamond_r, center),
        (center + diamond_thin, center + diamond_thin),
        (center, center + diamond_r),
        (center - diamond_thin, center + diamond_thin),
        (center - diamond_r, center),
        (center - diamond_thin, center - diamond_thin),
    ]
    # Outer glow
    glow_r = 28
    draw.ellipse([center - glow_r, center - glow_r, center + glow_r, center + glow_r], fill=(56, 189, 248, 70))
    draw.polygon(poly, fill=(255, 255, 255, 255))
    draw.ellipse([center - 6, center - 6, center + 6, center + 6], fill=(56, 189, 248, 255))

    # Precision calibration dots
    draw.ellipse([54, 76, 66, 88], fill=(129, 140, 248, 255))
    draw.ellipse([size - 66, size - 88, size - 54, size - 76], fill=(34, 211, 238, 255))

    # Save PNG
    png_path = os.path.join(output_dir, "favicon.png")
    img.save(png_path, "PNG")
    print(f"Saved: {png_path}")

    # Also save as logo.png
    logo_png_path = os.path.join(output_dir, "logo.png")
    img.save(logo_png_path, "PNG")
    print(f"Saved: {logo_png_path}")

    # Save multi-size ICO
    ico_path = os.path.join(output_dir, "favicon.ico")
    img.save(ico_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
    print(f"Saved: {ico_path}")

if __name__ == "__main__":
    static_images = os.path.abspath("app/web/static/images")
    static_dir = os.path.abspath("app/web/static")
    os.makedirs(static_images, exist_ok=True)

    svg_content = create_svg()
    
    # Save SVG logo
    svg_logo_path = os.path.join(static_images, "logo.svg")
    with open(svg_logo_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"Saved: {svg_logo_path}")

    # Save SVG favicon
    svg_fav_path = os.path.join(static_dir, "favicon.svg")
    with open(svg_fav_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"Saved: {svg_fav_path}")

    # Generate PNG & ICO
    generate_png_and_ico(static_dir)
    generate_png_and_ico(static_images)
