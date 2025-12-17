from PIL import Image
from io import BytesIO
from typing import Optional, Tuple
import os
import aiofiles
from app.config import get_settings
from app.utils.security import generate_random_string
import logging

settings = get_settings()
logger = logging.getLogger(__name__)

# 图片处理安全限制
MAX_IMAGE_PIXELS = 50_000_000  # 最大5000万像素（约7000x7000）
MAX_IMAGE_DIMENSION = 10000   # 单边最大10000像素
Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS  # 设置PIL全局限制


def compress_image(
    content: bytes,
    quality: int = 85,
    max_dimension: Optional[int] = None
) -> Tuple[bytes, int, int]:
    """
    Compress image and optionally resize.
    Returns: (compressed_content, width, height)
    """
    img = Image.open(BytesIO(content))
    
    # Get original dimensions
    width, height = img.size
    
    # Convert RGBA to RGB for JPEG (JPEG doesn't support alpha)
    if img.mode in ('RGBA', 'LA', 'P'):
        # Create white background
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Resize if needed
    if max_dimension and (width > max_dimension or height > max_dimension):
        ratio = min(max_dimension / width, max_dimension / height)
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        width, height = new_width, new_height
    
    # Save compressed
    output = BytesIO()
    img.save(output, format='JPEG', quality=quality, optimize=True)
    
    return output.getvalue(), width, height


def process_image(
    content: bytes,
    extension: str,
    quality: int = 85,
    max_dimension: Optional[int] = None
) -> Tuple[bytes, int, int, str]:
    """
    Process uploaded image: compress and get dimensions.
    Returns: (processed_content, width, height, final_extension)
    """
    try:
        img = Image.open(BytesIO(content))
        width, height = img.size
        original_format = img.format
        
        # 安全检查：防止超大图片导致内存溢出
        if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
            logger.warning(f"Image too large: {width}x{height}, max allowed: {MAX_IMAGE_DIMENSION}")
            # 强制缩小到最大尺寸
            ratio = min(MAX_IMAGE_DIMENSION / width, MAX_IMAGE_DIMENSION / height)
            new_width = int(width * ratio)
            new_height = int(height * ratio)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            width, height = new_width, new_height
        
        # For GIF, preserve animation (don't compress)
        if extension == 'gif' and getattr(img, 'is_animated', False):
            return content, width, height, extension
        
        # For WebP, PNG with transparency, keep format
        if extension in ('webp', 'png'):
            if img.mode in ('RGBA', 'LA', 'P'):
                output = BytesIO()
                if extension == 'webp':
                    img.save(output, format='WEBP', quality=quality, optimize=True)
                else:
                    img.save(output, format='PNG', optimize=True)
                return output.getvalue(), width, height, extension
        
        # Resize if needed
        if max_dimension and (width > max_dimension or height > max_dimension):
            ratio = min(max_dimension / width, max_dimension / height)
            new_width = int(width * ratio)
            new_height = int(height * ratio)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            width, height = new_width, new_height
        
        # Compress based on format
        output = BytesIO()
        
        if extension == 'webp':
            img.save(output, format='WEBP', quality=quality, optimize=True)
        elif extension == 'png':
            img.save(output, format='PNG', optimize=True)
        else:
            # Convert to RGB for JPEG
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                if img.mode == 'RGBA':
                    background.paste(img, mask=img.split()[-1])
                else:
                    background.paste(img)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            img.save(output, format='JPEG', quality=quality, optimize=True)
            extension = 'jpg'
        
        return output.getvalue(), width, height, extension
        
    except Exception as e:
        logger.error(f"Image processing error: {e}")
        # Return original if processing fails
        try:
            img = Image.open(BytesIO(content))
            return content, img.size[0], img.size[1], extension
        except:
            return content, 0, 0, extension


async def save_image_local(content: bytes, filename: str) -> str:
    """
    Save image to local storage.
    Returns the file path.
    """
    # Create upload directory if not exists
    upload_dir = settings.upload_path
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, filename)
    
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)
    
    return file_path


async def delete_image_local(filename: str) -> bool:
    """Delete image from local storage."""
    try:
        file_path = os.path.join(settings.upload_path, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception as e:
        logger.error(f"Error deleting file {filename}: {e}")
        return False


def generate_unique_filename(extension: str) -> str:
    """Generate a unique 8-character filename."""
    return f"{generate_random_string(8)}.{extension}"


def get_image_dimensions(content: bytes) -> Tuple[int, int]:
    """Get image width and height."""
    try:
        img = Image.open(BytesIO(content))
        return img.size
    except:
        return 0, 0
