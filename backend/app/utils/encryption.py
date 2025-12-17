"""
Encryption utilities for secure credential storage.
Uses AES-256-GCM for authenticated encryption.
"""
import os
import json
import base64
from typing import Any, Dict, Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from app.config import get_settings


def get_encryption_key() -> bytes:
    """
    Get or derive the encryption key from environment variable.
    The key should be a 32-byte (256-bit) key encoded in base64.
    If not set, derives a key from the app secret key (not recommended for production).
    """
    settings = get_settings()
    
    # Try to get dedicated encryption key
    encryption_key = os.environ.get("BACKUP_ENCRYPTION_KEY")
    
    if encryption_key:
        try:
            key = base64.b64decode(encryption_key)
            if len(key) == 32:
                return key
        except Exception:
            pass
    
    # Fall back to deriving from app secret key (not ideal but works)
    # Use PBKDF2 to derive a proper key from the secret
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"backup_encryption_salt_v1",  # Fixed salt for deterministic derivation
        iterations=100000,
    )
    return kdf.derive(settings.app_secret_key.encode())


def encrypt_config(config: Dict[str, Any]) -> str:
    """
    Encrypt a configuration dictionary using AES-256-GCM.
    
    Args:
        config: Dictionary containing configuration data
        
    Returns:
        Base64-encoded encrypted string containing nonce + ciphertext + tag
    """
    key = get_encryption_key()
    aesgcm = AESGCM(key)
    
    # Generate a random 12-byte nonce
    nonce = os.urandom(12)
    
    # Convert config to JSON bytes
    plaintext = json.dumps(config, ensure_ascii=False).encode('utf-8')
    
    # Encrypt with authentication
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    
    # Combine nonce + ciphertext and encode as base64
    encrypted_data = nonce + ciphertext
    return base64.b64encode(encrypted_data).decode('utf-8')


def decrypt_config(encrypted_str: str) -> Dict[str, Any]:
    """
    Decrypt an encrypted configuration string.
    
    Args:
        encrypted_str: Base64-encoded encrypted string
        
    Returns:
        Decrypted configuration dictionary
        
    Raises:
        ValueError: If decryption fails
    """
    try:
        key = get_encryption_key()
        aesgcm = AESGCM(key)
        
        # Decode from base64
        encrypted_data = base64.b64decode(encrypted_str)
        
        # Extract nonce (first 12 bytes) and ciphertext
        nonce = encrypted_data[:12]
        ciphertext = encrypted_data[12:]
        
        # Decrypt
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        
        # Parse JSON
        return json.loads(plaintext.decode('utf-8'))
    except Exception as e:
        raise ValueError(f"Failed to decrypt configuration: {str(e)}")


def mask_sensitive_value(value: str, visible_chars: int = 4) -> str:
    """
    Mask a sensitive string value, showing only the last few characters.
    
    Args:
        value: The sensitive string to mask
        visible_chars: Number of characters to show at the end
        
    Returns:
        Masked string like "****abcd"
    """
    if not value:
        return ""
    
    if len(value) <= visible_chars:
        return "*" * len(value)
    
    return "*" * (len(value) - visible_chars) + value[-visible_chars:]


def mask_config(config: Dict[str, Any], sensitive_fields: Optional[list] = None) -> Dict[str, Any]:
    """
    Mask sensitive fields in a configuration dictionary.
    
    Args:
        config: Configuration dictionary
        sensitive_fields: List of field names to mask. If None, uses default list.
        
    Returns:
        New dictionary with sensitive fields masked
    """
    if sensitive_fields is None:
        sensitive_fields = [
            "password", "secret", "key", "token", "credential",
            "access_key", "secret_key", "private_key", "api_key",
            "access_key_id", "secret_access_key", "access_key_secret"
        ]
    
    masked = {}
    for key, value in config.items():
        if isinstance(value, dict):
            masked[key] = mask_config(value, sensitive_fields)
        elif isinstance(value, str):
            # Check if this field should be masked
            key_lower = key.lower()
            should_mask = any(sf in key_lower for sf in sensitive_fields)
            masked[key] = mask_sensitive_value(value) if should_mask else value
        else:
            masked[key] = value
    
    return masked


def generate_encryption_key() -> str:
    """
    Generate a new random encryption key.
    
    Returns:
        Base64-encoded 32-byte key suitable for BACKUP_ENCRYPTION_KEY env var
    """
    key = os.urandom(32)
    return base64.b64encode(key).decode('utf-8')
