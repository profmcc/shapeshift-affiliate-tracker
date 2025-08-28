#!/usr/bin/env python3
"""
Simple script to create placeholder PNG icons for the Chrome extension.
Note: This creates basic colored squares as placeholders.
For production, you should create proper PNG icons.
"""

import os
from PIL import Image, ImageDraw

def create_icon(size, filename):
    """Create a simple colored square icon"""
    # Create a new image with the specified size
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Create a gradient-like effect with multiple colors
    colors = [
        (102, 126, 234),  # Blue
        (118, 75, 162),   # Purple
        (76, 175, 80),    # Green
        (33, 150, 243),   # Light Blue
    ]
    
    # Draw colored rectangles
    segment_size = size // 4
    for i in range(4):
        for j in range(4):
            color = colors[(i + j) % len(colors)]
            x1 = i * segment_size
            y1 = j * segment_size
            x2 = (i + 1) * segment_size
            y2 = (j + 1) * segment_size
            draw.rectangle([x1, y1, x2, y2], fill=color)
    
    # Add a simple "B" letter in the center
    try:
        # Try to use a default font
        draw.text((size//2 - 10, size//2 - 10), "B", fill=(255, 255, 255, 255))
    except:
        # If font not available, just draw a white circle
        center = size // 2
        radius = size // 6
        draw.ellipse([center - radius, center - radius, center + radius, center + radius], 
                     fill=(255, 255, 255, 255))
    
    # Save the icon
    img.save(filename, 'PNG')
    print(f"✅ Created {filename} ({size}x{size})")

def main():
    """Create all required icon sizes"""
    icon_sizes = [16, 48, 128]
    
    # Ensure icons directory exists
    os.makedirs('icons', exist_ok=True)
    
    # Create icons for each size
    for size in icon_sizes:
        filename = f"icons/icon{size}.png"
        create_icon(size, filename)
    
    print("\n🎉 All icons created successfully!")
    print("📁 Icons are in the 'icons/' directory")
    print("💡 For production, replace these with proper PNG icons")

if __name__ == "__main__":
    main()

