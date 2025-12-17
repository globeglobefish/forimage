"""
Captcha Service
Generates and validates image captchas for security-sensitive operations.
"""
import random
import string
import base64
from io import BytesIO
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import logging

logger = logging.getLogger(__name__)

# In-memory captcha storage (use Redis in production for distributed systems)
_captcha_store: dict = {}


def generate_captcha_text(length: int = 4) -> str:
    """Generate random captcha text (letters and numbers, excluding confusing chars)."""
    # Exclude confusing characters: 0, O, 1, I, l
    chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    return ''.join(random.choice(chars) for _ in range(length))


def generate_captcha_image(text: str, width: int = 150, height: int = 50) -> bytes:
    """Generate a captcha image with noise and distortion."""
    # Create image with gradient background
    image = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    
    # Add gradient background
    for y in range(height):
        r = 240 + random.randint(-10, 10)
        g = 240 + random.randint(-10, 10)
        b = 250 + random.randint(-5, 5)
        for x in range(width):
            draw.point((x, y), fill=(r, g, b))
    
    # Try to use a font, fallback to default
    font_size = 32
    try:
        # Try common system fonts
        font_paths = [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
            'C:/Windows/Fonts/arial.ttf',
            'C:/Windows/Fonts/Arial.ttf',
        ]
        font = None
        for path in font_paths:
            try:
                font = ImageFont.truetype(path, font_size)
                break
            except:
                continue
        if not font:
            font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()
    
    # Draw each character with random position and rotation
    char_width = width // (len(text) + 1)
    for i, char in enumerate(text):
        x = char_width * (i + 0.5) + random.randint(-5, 5)
        y = height // 2 - font_size // 2 + random.randint(-5, 5)
        
        # Random color for each character
        color = (
            random.randint(0, 100),
            random.randint(0, 100),
            random.randint(100, 150)
        )
        
        # Create a small image for the character and rotate it
        char_img = Image.new('RGBA', (font_size + 10, font_size + 10), (255, 255, 255, 0))
        char_draw = ImageDraw.Draw(char_img)
        char_draw.text((5, 5), char, font=font, fill=color)
        
        # Rotate the character
        angle = random.randint(-25, 25)
        char_img = char_img.rotate(angle, expand=True, fillcolor=(255, 255, 255, 0))
        
        # Paste onto main image
        image.paste(char_img, (int(x), int(y)), char_img)
    
    # Add noise lines
    for _ in range(random.randint(3, 5)):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        color = (
            random.randint(150, 200),
            random.randint(150, 200),
            random.randint(150, 200)
        )
        draw.line([(x1, y1), (x2, y2)], fill=color, width=1)
    
    # Add noise dots
    for _ in range(random.randint(50, 100)):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        color = (
            random.randint(100, 200),
            random.randint(100, 200),
            random.randint(100, 200)
        )
        draw.point((x, y), fill=color)
    
    # Apply slight blur
    image = image.filter(ImageFilter.SMOOTH)
    
    # Convert to bytes
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    return buffer.getvalue()


def create_captcha(captcha_id: str) -> Tuple[str, str]:
    """
    Create a new captcha and store it.
    Returns: (captcha_id, base64_image)
    """
    text = generate_captcha_text()
    image_bytes = generate_captcha_image(text)
    
    # Store captcha (expires after 5 minutes - handled by cleanup or Redis TTL)
    _captcha_store[captcha_id] = {
        'text': text.upper(),
        'created_at': __import__('time').time()
    }
    
    # Clean up old captchas (older than 5 minutes)
    current_time = __import__('time').time()
    expired_keys = [
        k for k, v in _captcha_store.items() 
        if current_time - v['created_at'] > 300
    ]
    for k in expired_keys:
        del _captcha_store[k]
    
    # Return base64 encoded image
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    return captcha_id, f"data:image/png;base64,{base64_image}"


def verify_captcha(captcha_id: str, user_input: str) -> bool:
    """
    Verify captcha input.
    Captcha is consumed after verification (one-time use).
    """
    if not captcha_id or not user_input:
        return False
    
    captcha_data = _captcha_store.get(captcha_id)
    if not captcha_data:
        return False
    
    # Check if expired (5 minutes)
    current_time = __import__('time').time()
    if current_time - captcha_data['created_at'] > 300:
        del _captcha_store[captcha_id]
        return False
    
    # Verify (case-insensitive)
    is_valid = captcha_data['text'] == user_input.upper().strip()
    
    # Always consume the captcha after verification attempt
    del _captcha_store[captcha_id]
    
    return is_valid


async def create_captcha_redis(captcha_id: str) -> Tuple[str, str]:
    """
    Create captcha using Redis for storage (for distributed systems).
    Falls back to in-memory if Redis is not available.
    """
    from app.redis import get_redis
    
    redis = get_redis()
    if not redis:
        return create_captcha(captcha_id)
    
    text = generate_captcha_text()
    image_bytes = generate_captcha_image(text)
    
    # Store in Redis with 5 minute expiry
    await redis.setex(f"captcha:{captcha_id}", 300, text.upper())
    
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    return captcha_id, f"data:image/png;base64,{base64_image}"


async def verify_captcha_redis(captcha_id: str, user_input: str) -> bool:
    """
    Verify captcha using Redis storage.
    Falls back to in-memory if Redis is not available.
    """
    from app.redis import get_redis
    
    redis = get_redis()
    if not redis:
        return verify_captcha(captcha_id, user_input)
    
    if not captcha_id or not user_input:
        return False
    
    key = f"captcha:{captcha_id}"
    stored_text = await redis.get(key)
    
    if not stored_text:
        return False
    
    # Always delete after verification attempt (one-time use)
    await redis.delete(key)
    
    # Handle both bytes (real Redis) and string (FakeRedis) responses
    if isinstance(stored_text, bytes):
        stored_text = stored_text.decode('utf-8')
    
    return stored_text == user_input.upper().strip()
