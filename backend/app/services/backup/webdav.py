"""
WebDAV backup backend implementation.
"""
import os
import time
import hashlib
from typing import List, Optional
from datetime import datetime
from xml.etree import ElementTree

import aiohttp
from aiohttp import BasicAuth

from app.services.backup.base import (
    BackupBackend, BackupResult, FileInfo, ConnectionTestResult
)


class WebDAVBackend(BackupBackend):
    """WebDAV backup backend using aiohttp."""
    
    def __init__(
        self,
        url: str,
        username: str,
        password: str,
        remote_path: str = "/",
    ):
        self.url = url.rstrip("/")
        self.username = username
        self.password = password
        self.remote_path = remote_path.rstrip("/") or ""
        self._session: Optional[aiohttp.ClientSession] = None
    
    @property
    def protocol_type(self) -> str:
        return "webdav"
    
    async def connect(self) -> bool:
        """Initialize WebDAV session."""
        try:
            import ssl
            
            auth = BasicAuth(self.username, self.password)
            
            # Create SSL context that accepts self-signed certificates
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(
                ssl=ssl_context,
                timeout=aiohttp.ClientTimeout(total=30, connect=10, sock_read=30)
            )
            
            self._session = aiohttp.ClientSession(
                auth=auth,
                connector=connector,
                timeout=aiohttp.ClientTimeout(total=60, connect=10, sock_read=30)
            )
            return True
        except Exception as e:
            raise ConnectionError(f"WebDAV session initialization failed: {str(e)}")
    
    async def disconnect(self) -> None:
        """Close WebDAV session."""
        if self._session:
            await self._session.close()
            self._session = None
    
    def _get_full_url(self, remote_path: str) -> str:
        """Get full WebDAV URL."""
        path = remote_path.lstrip("/")
        if self.remote_path:
            return f"{self.url}{self.remote_path}/{path}"
        return f"{self.url}/{path}"
    
    async def upload(self, local_path: str, remote_path: str) -> BackupResult:
        """Upload a file to WebDAV server."""
        url = self._get_full_url(remote_path)
        filename = os.path.basename(local_path)
        
        try:
            # Ensure directory exists
            dir_path = os.path.dirname(remote_path)
            if dir_path:
                await self.ensure_directory(dir_path)
            
            # Read file and calculate checksum
            with open(local_path, "rb") as f:
                content = f.read()
            
            checksum = hashlib.md5(content).hexdigest()
            
            # Upload file
            async with self._session.put(url, data=content) as response:
                if response.status not in (200, 201, 204):
                    raise Exception(f"Upload failed with status {response.status}")
            
            return BackupResult(
                success=True,
                filename=filename,
                bytes_transferred=len(content),
                remote_path=remote_path,
                checksum=checksum,
            )
        except Exception as e:
            return BackupResult(
                success=False,
                filename=filename,
                error_message=str(e),
            )
    
    async def upload_bytes(self, content: bytes, remote_path: str) -> BackupResult:
        """Upload bytes directly to WebDAV server."""
        url = self._get_full_url(remote_path)
        filename = os.path.basename(remote_path)
        
        try:
            # Ensure directory exists
            dir_path = os.path.dirname(remote_path)
            if dir_path:
                await self.ensure_directory(dir_path)
            
            checksum = hashlib.md5(content).hexdigest()
            
            # Upload content
            async with self._session.put(url, data=content) as response:
                if response.status not in (200, 201, 204):
                    raise Exception(f"Upload failed with status {response.status}")
            
            return BackupResult(
                success=True,
                filename=filename,
                bytes_transferred=len(content),
                remote_path=remote_path,
                checksum=checksum,
            )
        except Exception as e:
            return BackupResult(
                success=False,
                filename=filename,
                error_message=str(e),
            )
    
    async def download(self, remote_path: str, local_path: str) -> BackupResult:
        """Download a file from WebDAV server."""
        url = self._get_full_url(remote_path)
        filename = os.path.basename(remote_path)
        
        try:
            # Ensure local directory exists
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # Download file
            async with self._session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"Download failed with status {response.status}")
                content = await response.read()
            
            # Write to local file
            with open(local_path, "wb") as f:
                f.write(content)
            
            checksum = hashlib.md5(content).hexdigest()
            
            return BackupResult(
                success=True,
                filename=filename,
                bytes_transferred=len(content),
                remote_path=remote_path,
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
        url = self._get_full_url(remote_path)
        filename = os.path.basename(remote_path)
        
        try:
            async with self._session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"Download failed with status {response.status}")
                content = await response.read()
            
            checksum = hashlib.md5(content).hexdigest()
            
            result = BackupResult(
                success=True,
                filename=filename,
                bytes_transferred=len(content),
                remote_path=remote_path,
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
        """Delete a file from WebDAV server."""
        url = self._get_full_url(remote_path)
        try:
            async with self._session.delete(url) as response:
                return response.status in (200, 204)
        except Exception:
            return False
    
    async def exists(self, remote_path: str) -> bool:
        """Check if file exists on WebDAV server."""
        url = self._get_full_url(remote_path)
        try:
            async with self._session.head(url) as response:
                return response.status == 200
        except Exception:
            return False
    
    async def list_files(self, remote_path: str = "/") -> List[FileInfo]:
        """List files in WebDAV directory using PROPFIND."""
        url = self._get_full_url(remote_path)
        files = []
        
        propfind_body = """<?xml version="1.0" encoding="utf-8"?>
        <D:propfind xmlns:D="DAV:">
            <D:prop>
                <D:displayname/>
                <D:getcontentlength/>
                <D:getlastmodified/>
                <D:resourcetype/>
            </D:prop>
        </D:propfind>"""
        
        try:
            headers = {"Depth": "1", "Content-Type": "application/xml"}
            async with self._session.request(
                "PROPFIND", url, data=propfind_body, headers=headers
            ) as response:
                if response.status not in (200, 207):
                    return files
                
                content = await response.text()
                
                # Parse XML response
                root = ElementTree.fromstring(content)
                ns = {"D": "DAV:"}
                
                for response_elem in root.findall(".//D:response", ns):
                    href = response_elem.find("D:href", ns)
                    if href is None:
                        continue
                    
                    propstat = response_elem.find("D:propstat", ns)
                    if propstat is None:
                        continue
                    
                    prop = propstat.find("D:prop", ns)
                    if prop is None:
                        continue
                    
                    # Get filename
                    displayname = prop.find("D:displayname", ns)
                    filename = displayname.text if displayname is not None and displayname.text else href.text.rstrip("/").split("/")[-1]
                    
                    if not filename:
                        continue
                    
                    # Check if directory
                    resourcetype = prop.find("D:resourcetype", ns)
                    is_dir = resourcetype is not None and resourcetype.find("D:collection", ns) is not None
                    
                    # Get size
                    size_elem = prop.find("D:getcontentlength", ns)
                    size = int(size_elem.text) if size_elem is not None and size_elem.text else 0
                    
                    # Get modified time
                    modified_elem = prop.find("D:getlastmodified", ns)
                    modified_time = None
                    if modified_elem is not None and modified_elem.text:
                        try:
                            # Parse RFC 2822 date format
                            from email.utils import parsedate_to_datetime
                            modified_time = parsedate_to_datetime(modified_elem.text)
                        except Exception:
                            pass
                    
                    files.append(FileInfo(
                        filename=filename,
                        size=size,
                        modified_time=modified_time,
                        is_directory=is_dir,
                    ))
        except Exception:
            pass
        
        return files
    
    async def ensure_directory(self, remote_path: str) -> bool:
        """Ensure directory exists on WebDAV server using MKCOL."""
        parts = remote_path.strip("/").split("/")
        current = ""
        
        try:
            for part in parts:
                current = f"{current}/{part}"
                url = self._get_full_url(current)
                
                # Try to create directory
                async with self._session.request("MKCOL", url) as response:
                    # 201 = created, 405 = already exists
                    if response.status not in (201, 405):
                        pass  # Continue anyway
            return True
        except Exception:
            return False
    
    async def test_connection(self) -> ConnectionTestResult:
        """Test WebDAV connection."""
        start_time = time.time()
        temp_session = None
        
        try:
            import asyncio
            import ssl
            
            # Create a fresh session for testing
            auth = BasicAuth(self.username, self.password)
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(
                ssl=ssl_context,
                timeout=aiohttp.ClientTimeout(total=30, connect=10, sock_read=30)
            )
            
            temp_session = aiohttp.ClientSession(
                auth=auth,
                connector=connector,
                timeout=aiohttp.ClientTimeout(total=60, connect=10, sock_read=30)
            )
            
            # Try to access root path
            url = self._get_full_url("")
            async with asyncio.timeout(30):
                async with temp_session.request(
                    "PROPFIND", url, headers={"Depth": "0"}
                ) as response:
                    if response.status not in (200, 207):
                        raise Exception(f"PROPFIND failed with status {response.status}")
            
            latency = (time.time() - start_time) * 1000
            
            return ConnectionTestResult(
                success=True,
                message="WebDAV connection successful",
                latency_ms=latency,
                details={
                    "url": self.url,
                    "remote_path": self.remote_path,
                    "username": self.username,
                }
            )
        except asyncio.TimeoutError:
            return ConnectionTestResult(
                success=False,
                message=f"WebDAV connection timeout to {self.url}",
                latency_ms=None,
                details={
                    "url": self.url,
                    "error": "Connection timeout",
                }
            )
        except Exception as e:
            error_msg = str(e)
            # Provide more specific error messages
            if "401" in error_msg or "Unauthorized" in error_msg:
                return ConnectionTestResult(
                    success=False,
                    message="WebDAV authentication failed - check username and password",
                    latency_ms=None,
                    details={
                        "url": self.url,
                        "username": self.username,
                        "error": "Authentication failed",
                    }
                )
            elif "403" in error_msg or "Forbidden" in error_msg:
                return ConnectionTestResult(
                    success=False,
                    message="WebDAV access forbidden - check permissions",
                    latency_ms=None,
                    details={
                        "url": self.url,
                        "error": "Permission denied",
                    }
                )
            elif "404" in error_msg or "Not Found" in error_msg:
                return ConnectionTestResult(
                    success=False,
                    message=f"WebDAV path not found: {self.remote_path}",
                    latency_ms=None,
                    details={
                        "url": self.url,
                        "remote_path": self.remote_path,
                        "error": "Path does not exist",
                    }
                )
            else:
                return ConnectionTestResult(
                    success=False,
                    message=f"WebDAV connection failed: {error_msg}",
                    latency_ms=None,
                    details={
                        "url": self.url,
                        "error": error_msg,
                    }
                )
        finally:
            # Clean up temporary session
            if temp_session:
                await temp_session.close()
