
from PIL import Image, ImageDraw, ImageFont
import os

def create_gradient_background(size):
    """Create a gradient background"""
    img = Image.new('RGB', (size, size))
    draw = ImageDraw.Draw(img)
    
    # Create gradient from indigo to purple
    for y in range(size):
        # Color transition from #6366f1 (indigo) to #8b5cf6 (purple)
        r = int(99 + (139 - 99) * y / size)
        g = int(102 + (92 - 102) * y / size)
        b = int(241 + (246 - 241) * y / size)
        draw.rectangle([(0, y), (size, y + 1)], fill=(r, g, b))
    
    return img

def add_emoji_text(img, emoji, size):
    """Add emoji text to image"""
    draw = ImageDraw.Draw(img)
    
    # Try to use a font that supports emoji
    font_size = int(size * 0.6)
    try:
        # Try different font paths
        font_paths = [
            '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf',
            '/System/Library/Fonts/Apple Color Emoji.ttc',
            'seguiemj.ttf',  # Windows
        ]
        font = None
        for path in font_paths:
            if os.path.exists(path):
                try:
                    font = ImageFont.truetype(path, font_size)
                    break
                except:
                    continue
        
        if font is None:
            font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', font_size)
    except:
        font = ImageFont.load_default()
    
    # Get text bounding box
    bbox = draw.textbbox((0, 0), emoji, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Center the text
    x = (size - text_width) // 2
    y = (size - text_height) // 2 - bbox[1]
    
    # Add white shadow for better visibility
    shadow_offset = max(2, size // 100)
    draw.text((x + shadow_offset, y + shadow_offset), emoji, fill='white', font=font)
    draw.text((x, y), emoji, fill='white', font=font)
    
    return img

def create_maskable_icon(img, size):
    """Create a maskable icon with safe zone padding"""
    # Maskable icons need 40% padding (safe zone)
    safe_zone = int(size * 0.4)
    padded_size = size + safe_zone * 2
    
    # Create new image with padding
    padded = Image.new('RGB', (padded_size, padded_size))
    
    # Fill with gradient
    draw = ImageDraw.Draw(padded)
    for y in range(padded_size):
        r = int(99 + (139 - 99) * y / padded_size)
        g = int(102 + (92 - 102) * y / padded_size)
        b = int(241 + (246 - 241) * y / padded_size)
        draw.rectangle([(0, y), (padded_size, y + 1)], fill=(r, g, b))
    
    # Paste original image in center
    padded.paste(img, (safe_zone, safe_zone))
    
    # Resize back to original size
    return padded.resize((size, size), Image.Resampling.LANCZOS)

# Create icons directory
os.makedirs('static/icons', exist_ok=True)

# Generate icons for different sizes
sizes = [72, 96, 128, 144, 152, 192, 384, 512]

for size in sizes:
    # Create regular icon
    img = create_gradient_background(size)
    img = add_emoji_text(img, '🎓', size)
    img.save(f'static/icons/icon-{size}x{size}.png', 'PNG')
    print(f'Generated icon-{size}x{size}.png')
    
    # Create maskable icon
    maskable = create_maskable_icon(img, size)
    maskable.save(f'static/icons/icon-{size}x{size}-maskable.png', 'PNG')
    print(f'Generated icon-{size}x{size}-maskable.png')

print('\nAll icons generated successfully!')
print('Icons saved to static/icons/')
