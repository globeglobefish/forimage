import magic
from typing import Optional
from fastapi import UploadFile, HTTPException, status
from app.config import get_settings
import re

settings = get_settings()

ALLOWED_MIME_TYPES = {
    "image/jpeg": ["jpg", "jpeg"],
    "image/png": ["png"],
    "image/gif": ["gif"],
    "image/webp": ["webp"],
}

MAGIC_BYTES = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"GIF87a": "image/gif",
    b"GIF89a": "image/gif",
    b"RIFF": "image/webp",  # WebP starts with RIFF
}


def validate_image_file(file: UploadFile, max_size: int, allowed_extensions: list = None) -> str:
    """
    Validate uploaded image file.
    Returns extension if valid.
    Raises HTTPException if invalid.
    """
    # Use default if not provided
    if allowed_extensions is None:
        allowed_extensions = settings.allowed_extensions_list
    
    # Check filename
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided"
        )

    # Get extension from filename
    filename_parts = file.filename.rsplit(".", 1)
    if len(filename_parts) != 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename format"
        )
    
    extension = filename_parts[1].lower()
    
    # Check if extension is allowed
    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension '{extension}' is not allowed. Allowed: {', '.join(allowed_extensions)}"
        )

    return extension


async def validate_image_content(content: bytes, extension: str, max_size: int) -> tuple:
    """
    Validate image content by checking magic bytes and file size.
    Returns tuple of (mime_type, corrected_extension).
    
    如果文件扩展名与实际内容类型不匹配，会自动修正扩展名。
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Check file size
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds the limit of {max_size // 1024 // 1024}MB"
        )

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file"
        )

    # Detect MIME type using magic bytes
    detected_mime = None
    for magic_bytes, mime_type in MAGIC_BYTES.items():
        if content.startswith(magic_bytes):
            detected_mime = mime_type
            break
    
    # Special handling for WebP (RIFF....WEBP)
    if content[:4] == b"RIFF" and len(content) > 12 and content[8:12] == b"WEBP":
        detected_mime = "image/webp"

    if not detected_mime:
        # Fallback to python-magic
        try:
            detected_mime = magic.from_buffer(content, mime=True)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to detect file type"
            )

    # Verify MIME type is allowed
    if detected_mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{detected_mime}' is not allowed"
        )

    # Check if extension matches MIME type, auto-correct if not
    valid_extensions = ALLOWED_MIME_TYPES.get(detected_mime, [])
    if extension not in valid_extensions:
        # 自动修正扩展名为实际内容类型对应的扩展名
        corrected_extension = valid_extensions[0]  # 使用第一个有效扩展名
        logger.warning(
            f"Extension mismatch: filename has '.{extension}' but content is '{detected_mime}'. "
            f"Auto-correcting to '.{corrected_extension}'"
        )
        return detected_mime, corrected_extension
    
    return detected_mime, extension


def sanitize_filename(filename: str) -> str:
    """Remove potentially dangerous characters from filename."""
    # Remove path separators and null bytes
    filename = filename.replace("/", "").replace("\\", "").replace("\x00", "")
    # Remove any non-printable characters
    filename = re.sub(r'[^\w\s.-]', '', filename)
    # Limit length
    return filename[:255]


def validate_ip_address(ip: str) -> bool:
    """Validate IP address format (IPv4 or IPv6)."""
    ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    ipv6_pattern = r'^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$'
    
    if re.match(ipv4_pattern, ip):
        parts = ip.split('.')
        return all(0 <= int(part) <= 255 for part in parts)
    
    return bool(re.match(ipv6_pattern, ip))
