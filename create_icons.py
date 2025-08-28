#!/usr/bin/env python3
"""
Create SVG icons for DeFi Data Snatcher extension
"""

import os


def create_svg_icon(size, filename):
    """Create a simple SVG icon with the specified size"""

    svg_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
    </linearGradient>
    <linearGradient id="grad2" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#ff6b6b;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#4ecdc4;stop-opacity:1" />
    </linearGradient>
  </defs>
  
  <!-- Background circle -->
  <circle cx="{size//2}" cy="{size//2}" r="{size//2-2}" fill="url(#grad1)" stroke="white" stroke-width="2"/>
  
  <!-- Diamond/Data symbol -->
  <polygon points="{size//2},{size//4} {size*3//4},{size//2} {size//2},{size*3//4} {size//4},{size//2}" 
           fill="url(#grad2)" stroke="white" stroke-width="1"/>
  
  <!-- Small data dots -->
  <circle cx="{size//3}" cy="{size//3}" r="2" fill="white"/>
  <circle cx="{size*2//3}" cy="{size//3}" r="2" fill="white"/>
  <circle cx="{size//3}" cy="{size*2//3}" r="2" fill="white"/>
  <circle cx="{size*2//3}" cy="{size*2//3}" r="2" fill="white"/>
</svg>"""

    with open(filename, "w") as f:
        f.write(svg_content)

    print(f"✅ Created {filename}")


def main():
    """Create all required icon sizes"""

    # Ensure icons directory exists
    if not os.path.exists("icons"):
        os.makedirs("icons")

    # Create icons for different sizes
    sizes = [16, 32, 48, 128]

    for size in sizes:
        svg_filename = f"icons/icon{size}.svg"

        # Create SVG
        create_svg_icon(size, svg_filename)

        print(f"📝 Note: icons/icon{size}.png needs to be converted from {svg_filename}")

    print("\n🎉 Icon creation complete!")
    print("📝 To convert SVGs to PNGs for Chrome Web Store:")
    print("   1. Use online converters:")
    print("      - https://convertio.co/svg-png/")
    print("      - https://cloudconvert.com/svg-to-png")
    print("   2. Or use command line tools:")
    print("      - ImageMagick: convert icon.svg icon.png")
    print("      - Inkscape: inkscape icon.svg --export-png=icon.png")
    print("\n💡 For Chrome Web Store, you need PNG files!")


if __name__ == "__main__":
    main()
