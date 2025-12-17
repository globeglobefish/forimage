"""
Factory for creating backup backend instances.
"""
from typing import Dict, Any
from app.services.backup.base import BackupBackend
from app.models.backup import BackupProtocol


def get_backup_backend(protocol: BackupProtocol, config: Dict[str, Any]) -> BackupBackend:
    """
    Create a backup backend instance based on protocol type.
    
    Args:
        protocol: The backup protocol type
        config: Protocol-specific configuration dictionary
        
    Returns:
        BackupBackend instance
        
    Raises:
        ValueError: If protocol is not supported
        ImportError: If required library is not installed
    """
    if protocol == BackupProtocol.FTP:
        from app.services.backup.ftp import FTPBackend
        return FTPBackend(
            host=config["host"],
            port=config.get("port", 21),
            username=config["username"],
            password=config.get("password", ""),
            remote_path=config.get("remote_path", "/"),
            passive_mode=config.get("passive_mode", True),
        )
    
    elif protocol == BackupProtocol.SFTP:
        from app.services.backup.sftp import SFTPBackend
        return SFTPBackend(
            host=config["host"],
            port=config.get("port", 22),
            username=config["username"],
            password=config.get("password"),
            private_key=config.get("private_key"),
            remote_path=config.get("remote_path", "/"),
        )
    
    elif protocol == BackupProtocol.S3:
        from app.services.backup.s3 import S3BackupBackend
        return S3BackupBackend(
            endpoint=config["endpoint"],
            access_key=config["access_key"],
            secret_key=config["secret_key"],
            bucket_name=config["bucket_name"],
            region=config.get("region"),
            prefix=config.get("prefix", ""),
            provider=config.get("provider", "custom"),
            path_style=config.get("path_style"),
        )
    
    elif protocol == BackupProtocol.WEBDAV:
        from app.services.backup.webdav import WebDAVBackend
        return WebDAVBackend(
            url=config["url"],
            username=config["username"],
            password=config["password"],
            remote_path=config.get("remote_path", "/"),
        )
    
    else:
        raise ValueError(f"Unsupported backup protocol: {protocol}")
