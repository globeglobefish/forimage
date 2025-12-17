"""
FTP backup backend implementation.
"""
import os
import time
import hashlib
import asyncio
from typing import List, Optional
from datetime import datetime
from io import BytesIO

import aioftp

from app.services.backup.base import (
    BackupBackend, BackupResult, FileInfo, ConnectionTestResult
)


class FTPBackend(BackupBackend):
    """FTP backup backend using aioftp."""
    
    def __init__(
        self,
        host: str,
        port: int = 21,
        username: str = "anonymous",
        password: str = "",
        remote_path: str = "/",
        passive_mode: bool = True,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.remote_path = remote_path.rstrip("/") or "/"
        self.passive_mode = passive_mode
        self._client: Optional[aioftp.Client] = None
    
    @property
    def protocol_type(self) -> str:
        return "ftp"
    
    async def connect(self) -> bool:
        """Establish FTP connection."""
        try:
            import asyncio
            
            self._client = aioftp.Client()
            
            # Connect with timeout
            await asyncio.wait_for(
                self._client.connect(self.host, self.port),
                timeout=30.0
            )
            
            # Login with timeout
            await asyncio.wait_for(
                self._client.login(self.username, self.password),
                timeout=30.0
            )
            
            # Set passive mode if configured
            if self.passive_mode:
                try:
                    await self._client.passive_mode()
                except Exception:
                    # Passive mode might not be supported, continue anyway
                    pass
            
            return True
        except asyncio.TimeoutError:
            self._client = None
            raise ConnectionError(f"FTP connection timeout to {self.host}:{self.port}")
        except Exception as e:
            self._client = None
            error_msg = str(e)
            # Provide more specific error messages
            if "530" in error_msg or "Login failed" in error_msg:
                raise ConnectionError(f"FTP authentication failed for user '{self.username}': {error_msg}")
            elif "Connection refused" in error_msg:
                raise ConnectionError(f"FTP connection refused by {self.host}:{self.port}")
            elif "Name or service not known" in error_msg:
                raise ConnectionError(f"FTP host '{self.host}' not found or unreachable")
            else:
                raise ConnectionError(f"FTP connection failed: {error_msg}")
    
    async def disconnect(self) -> None:
        """Close FTP connection."""
        if self._client:
            try:
                await self._client.quit()
            except Exception:
                pass
            finally:
                self._client = None
    
    def _get_full_path(self, remote_path: str) -> str:
        """Get full remote path including base path."""
        if remote_path.startswith("/"):
            return f"{self.remote_path}{remote_path}"
        return f"{self.remote_path}/{remote_path}"
    
    async def upload(self, local_path: str, remote_path: str) -> BackupResult:
        """Upload a file to FTP server."""
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
            await self._client.upload(local_path, full_path, write_into=True)
            
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
        """Upload bytes directly to FTP server."""
        full_path = self._get_full_path(remote_path)
        filename = os.path.basename(remote_path)
        
        try:
            # Ensure directory exists
            dir_path = os.path.dirname(full_path)
            if dir_path:
                await self.ensure_directory(dir_path)
            
            checksum = hashlib.md5(content).hexdigest()
            
            # Upload using stream
            stream = BytesIO(content)
            async with self._client.upload_stream(full_path) as ftp_stream:
                await ftp_stream.write(content)
            
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
        """Download a file from FTP server."""
        full_path = self._get_full_path(remote_path)
        filename = os.path.basename(remote_path)
        
        try:
            # Ensure local directory exists
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # Download file
            await self._client.download(full_path, local_path, write_into=True)
            
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
            content = b""
            async with self._client.download_stream(full_path) as stream:
                async for block in stream.iter_by_block():
                    content += block
            
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
        """Delete a file from FTP server."""
        full_path = self._get_full_path(remote_path)
        try:
            await self._client.remove(full_path)
            return True
        except Exception:
            return False
    
    async def exists(self, remote_path: str) -> bool:
        """Check if file exists on FTP server."""
        full_path = self._get_full_path(remote_path)
        try:
            await self._client.stat(full_path)
            return True
        except Exception:
            return False
    
    async def list_files(self, remote_path: str = "/") -> List[FileInfo]:
        """List files in FTP directory."""
        full_path = self._get_full_path(remote_path)
        files = []
        
        try:
            async for path, info in self._client.list(full_path):
                is_dir = info.get("type") == "dir"
                size = int(info.get("size", 0)) if not is_dir else 0
                
                # Parse modification time if available
                modify_str = info.get("modify")
                modified_time = None
                if modify_str:
                    try:
                        modified_time = datetime.strptime(modify_str, "%Y%m%d%H%M%S")
                    except ValueError:
                        pass
                
                files.append(FileInfo(
                    filename=path.name,
                    size=size,
                    modified_time=modified_time,
                    is_directory=is_dir,
                ))
        except Exception:
            pass
        
        return files
    
    async def ensure_directory(self, remote_path: str) -> bool:
        """Ensure directory exists on FTP server."""
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
                    await self._client.make_directory(current)
                except Exception:
                    # Directory might already exist
                    pass
            return True
        except Exception:
            return False
    
    async def test_connection(self) -> ConnectionTestResult:
        """Test FTP connection."""
        start_time = time.time()
        temp_client = None
        
        try:
            import asyncio
            
            # Always create a fresh connection for testing
            temp_client = aioftp.Client()
            
            await asyncio.wait_for(
                temp_client.connect(self.host, self.port),
                timeout=30.0
            )
            
            await asyncio.wait_for(
                temp_client.login(self.username, self.password),
                timeout=30.0
            )
            
            # Try to list remote path
            await asyncio.wait_for(
                temp_client.list(self.remote_path),
                timeout=10.0
            )
            
            latency = (time.time() - start_time) * 1000
            
            return ConnectionTestResult(
                success=True,
                message="FTP connection successful",
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
                message=f"FTP connection timeout to {self.host}:{self.port}",
                latency_ms=None,
                details={
                    "host": self.host,
                    "port": self.port,
                    "error": "Connection timeout",
                }
            )
        except Exception as e:
            error_msg = str(e)
            return ConnectionTestResult(
                success=False,
                message=f"FTP connection failed: {error_msg}",
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
            if temp_client:
                try:
                    await temp_client.quit()
                except Exception:
                    pass
