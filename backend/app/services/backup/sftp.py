"""
SFTP backup backend implementation.
"""
import os
import time
import hashlib
from typing import List, Optional
from datetime import datetime

import asyncssh

from app.services.backup.base import (
    BackupBackend, BackupResult, FileInfo, ConnectionTestResult
)


class SFTPBackend(BackupBackend):
    """SFTP backup backend using asyncssh."""
    
    def __init__(
        self,
        host: str,
        port: int = 22,
        username: str = "",
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        remote_path: str = "/",
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.private_key = private_key
        self.remote_path = remote_path.rstrip("/") or "/"
        self._conn: Optional[asyncssh.SSHClientConnection] = None
        self._sftp: Optional[asyncssh.SFTPClient] = None
    
    @property
    def protocol_type(self) -> str:
        return "sftp"
    
    async def connect(self) -> bool:
        """Establish SFTP connection."""
        try:
            connect_kwargs = {
                "host": self.host,
                "port": self.port,
                "username": self.username,
                "known_hosts": None,  # Disable host key checking
            }
            
            # Prefer private key over password
            if self.private_key:
                try:
                    connect_kwargs["client_keys"] = [asyncssh.import_private_key(self.private_key)]
                except Exception as e:
                    raise ValueError(f"Invalid private key: {str(e)}")
            elif self.password:
                connect_kwargs["password"] = self.password
            else:
                raise ValueError("Either password or private_key must be provided")
            
            # Attempt connection with timeout
            import asyncio
            self._conn = await asyncio.wait_for(
                asyncssh.connect(**connect_kwargs),
                timeout=30.0
            )
            self._sftp = await self._conn.start_sftp_client()
            return True
        except asyncio.TimeoutError:
            self._conn = None
            self._sftp = None
            raise ConnectionError(f"SFTP connection timeout to {self.host}:{self.port}")
        except asyncssh.PermissionDenied as e:
            self._conn = None
            self._sftp = None
            raise ConnectionError(f"SFTP authentication failed for user '{self.username}': {str(e)}")
        except asyncssh.HostKeyNotVerifiable as e:
            self._conn = None
            self._sftp = None
            raise ConnectionError(f"SFTP host key verification failed: {str(e)}")
        except Exception as e:
            self._conn = None
            self._sftp = None
            error_msg = str(e)
            # Provide more specific error messages
            if "Permission denied" in error_msg:
                raise ConnectionError(f"SFTP permission denied for user '{self.username}' on {self.host}: {error_msg}")
            elif "Connection refused" in error_msg:
                raise ConnectionError(f"SFTP connection refused by {self.host}:{self.port}")
            elif "Name or service not known" in error_msg or "getaddrinfo failed" in error_msg:
                raise ConnectionError(f"SFTP host '{self.host}' not found or unreachable")
            else:
                raise ConnectionError(f"SFTP connection failed: {error_msg}")
    
    async def disconnect(self) -> None:
        """Close SFTP connection."""
        if self._sftp:
            self._sftp.exit()
            self._sftp = None
        if self._conn:
            self._conn.close()
            await self._conn.wait_closed()
            self._conn = None
    
    def _get_full_path(self, remote_path: str) -> str:
        """Get full remote path including base path."""
        if remote_path.startswith("/"):
            return f"{self.remote_path}{remote_path}"
        return f"{self.remote_path}/{remote_path}"
    
    async def upload(self, local_path: str, remote_path: str) -> BackupResult:
        """Upload a file to SFTP server."""
        full_path = self._get_full_path(remote_path)
        filename = os.path.basename(local_path)
        
        try:
            # Ensure directory exists
            dir_path = os.path.dirname(full_path)
            if dir_path:
                await self.ensure_directory(dir_path)
            
            # Read file and calculate checksum
            with open(local_path, "rb") as f:
                content = f.read()
            
            checksum = hashlib.md5(content).hexdigest()
            
            # Upload file
            await self._sftp.put(local_path, full_path)
            
            return BackupResult(
                success=True,
                filename=filename,
                bytes_transferred=len(content),
                remote_path=full_path,
                checksum=checksum,
            )
        except Exception as e:
            return BackupResult(
                success=False,
                filename=filename,
                error_message=str(e),
            )
    
    async def upload_bytes(self, content: bytes, remote_path: str) -> BackupResult:
        """Upload bytes directly to SFTP server."""
        full_path = self._get_full_path(remote_path)
        filename = os.path.basename(remote_path)
        
        try:
            # Ensure directory exists
            dir_path = os.path.dirname(full_path)
            if dir_path:
                await self.ensure_directory(dir_path)
            
            checksum = hashlib.md5(content).hexdigest()
            
            # Write bytes directly
            async with self._sftp.open(full_path, "wb") as f:
                await f.write(content)
            
            return BackupResult(
                success=True,
                filename=filename,
                bytes_transferred=len(content),
                remote_path=full_path,
                checksum=checksum,
            )
        except Exception as e:
            return BackupResult(
                success=False,
                filename=filename,
                error_message=str(e),
            )
    
    async def download(self, remote_path: str, local_path: str) -> BackupResult:
        """Download a file from SFTP server."""
        full_path = self._get_full_path(remote_path)
        filename = os.path.basename(remote_path)
        
        try:
            # Ensure local directory exists
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # Download file
            await self._sftp.get(full_path, local_path)
            
            # Get file size and checksum
            with open(local_path, "rb") as f:
                content = f.read()
            
            checksum = hashlib.md5(content).hexdigest()
            
            return BackupResult(
                success=True,
                filename=filename,
                bytes_transferred=len(content),
                remote_path=full_path,
                checksum=checksum,
            )
        except Exception as e:
            return BackupResult(
                success=False,
                filename=filename,
                error_message=str(e),
            )
    
    async def download_bytes(self, remote_path: str) -> tuple[bytes, BackupResult]:
        """Download file content as bytes."""
        full_path = self._get_full_path(remote_path)
        filename = os.path.basename(remote_path)
        
        try:
            async with self._sftp.open(full_path, "rb") as f:
                content = await f.read()
            
            checksum = hashlib.md5(content).hexdigest()
            
            result = BackupResult(
                success=True,
                filename=filename,
                bytes_transferred=len(content),
                remote_path=full_path,
                checksum=checksum,
            )
            return content, result
        except Exception as e:
            result = BackupResult(
                success=False,
                filename=filename,
                error_message=str(e),
            )
            return b"", result
    
    async def delete(self, remote_path: str) -> bool:
        """Delete a file from SFTP server."""
        full_path = self._get_full_path(remote_path)
        try:
            await self._sftp.remove(full_path)
            return True
        except Exception:
            return False
    
    async def exists(self, remote_path: str) -> bool:
        """Check if file exists on SFTP server."""
        full_path = self._get_full_path(remote_path)
        try:
            await self._sftp.stat(full_path)
            return True
        except Exception:
            return False
    
    async def list_files(self, remote_path: str = "/") -> List[FileInfo]:
        """List files in SFTP directory."""
        full_path = self._get_full_path(remote_path)
        files = []
        
        try:
            async for entry in self._sftp.scandir(full_path):
                attrs = entry.attrs
                is_dir = attrs.type == asyncssh.FILEXFER_TYPE_DIRECTORY
                
                modified_time = None
                if attrs.mtime:
                    modified_time = datetime.fromtimestamp(attrs.mtime)
                
                files.append(FileInfo(
                    filename=entry.filename,
                    size=attrs.size or 0,
                    modified_time=modified_time,
                    is_directory=is_dir,
                ))
        except Exception:
            pass
        
        return files
    
    async def ensure_directory(self, remote_path: str) -> bool:
        """Ensure directory exists on SFTP server."""
        # Remove base path prefix if present
        if remote_path.startswith(self.remote_path):
            remote_path = remote_path[len(self.remote_path):]
        
        full_path = self._get_full_path(remote_path)
        
        try:
            # Try to create directory recursively
            parts = full_path.strip("/").split("/")
            current = ""
            for part in parts:
                current = f"{current}/{part}"
                try:
                    await self._sftp.mkdir(current)
                except Exception:
                    # Directory might already exist
                    pass
            return True
        except Exception:
            return False
    
    async def test_connection(self) -> ConnectionTestResult:
        """Test SFTP connection."""
        start_time = time.time()
        temp_conn = None
        temp_sftp = None
        
        try:
            # Always create a fresh connection for testing
            connect_kwargs = {
                "host": self.host,
                "port": self.port,
                "username": self.username,
                "known_hosts": None,  # Disable host key checking
            }
            
            if self.private_key:
                connect_kwargs["client_keys"] = [asyncssh.import_private_key(self.private_key)]
            elif self.password:
                connect_kwargs["password"] = self.password
            
            import asyncio
            temp_conn = await asyncio.wait_for(
                asyncssh.connect(**connect_kwargs),
                timeout=30.0
            )
            temp_sftp = await temp_conn.start_sftp_client()
            
            # Try to list remote path
            await temp_sftp.listdir(self.remote_path)
            
            latency = (time.time() - start_time) * 1000
            
            return ConnectionTestResult(
                success=True,
                message="SFTP connection successful",
                latency_ms=latency,
                details={
                    "host": self.host,
                    "port": self.port,
                    "remote_path": self.remote_path,
                    "username": self.username,
                }
            )
        except asyncio.TimeoutError:
            return ConnectionTestResult(
                success=False,
                message=f"SFTP connection timeout to {self.host}:{self.port}",
                latency_ms=None,
                details={
                    "host": self.host,
                    "port": self.port,
                    "error": "Connection timeout",
                }
            )
        except asyncssh.PermissionDenied as e:
            return ConnectionTestResult(
                success=False,
                message=f"SFTP authentication failed for user '{self.username}'",
                latency_ms=None,
                details={
                    "host": self.host,
                    "port": self.port,
                    "username": self.username,
                    "error": "Authentication failed - check username and password/key",
                }
            )
        except Exception as e:
            error_msg = str(e)
            return ConnectionTestResult(
                success=False,
                message=f"SFTP connection failed: {error_msg}",
                latency_ms=None,
                details={
                    "host": self.host,
                    "port": self.port,
                    "username": self.username,
                    "error": error_msg,
                }
            )
        finally:
            # Clean up temporary connection
            if temp_sftp:
                try:
                    temp_sftp.exit()
                except Exception:
                    pass
            if temp_conn:
                try:
                    temp_conn.close()
                    await temp_conn.wait_closed()
                except Exception:
                    pass
