"""
Abstract base class for backup backends.
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class BackupResult:
    """Result of a backup operation."""
    success: bool
    filename: str
    bytes_transferred: int = 0
    error_message: Optional[str] = None
    remote_path: Optional[str] = None
    checksum: Optional[str] = None


@dataclass
class FileInfo:
    """Information about a remote file."""
    filename: str
    size: int
    modified_time: Optional[datetime] = None
    checksum: Optional[str] = None
    is_directory: bool = False


@dataclass
class ConnectionTestResult:
    """Result of a connection test."""
    success: bool
    message: str
    latency_ms: Optional[float] = None
    details: Dict[str, Any] = field(default_factory=dict)


class BackupBackend(ABC):
    """Abstract base class for backup backends."""
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to remote storage.
        
        Returns:
            True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to remote storage."""
        pass
    
    @abstractmethod
    async def upload(self, local_path: str, remote_path: str) -> BackupResult:
        """
        Upload a file to remote storage.
        
        Args:
            local_path: Path to local file
            remote_path: Destination path on remote storage
            
        Returns:
            BackupResult with operation details
        """
        pass
    
    @abstractmethod
    async def upload_bytes(self, content: bytes, remote_path: str) -> BackupResult:
        """
        Upload bytes directly to remote storage.
        
        Args:
            content: File content as bytes
            remote_path: Destination path on remote storage
            
        Returns:
            BackupResult with operation details
        """
        pass
    
    @abstractmethod
    async def download(self, remote_path: str, local_path: str) -> BackupResult:
        """
        Download a file from remote storage.
        
        Args:
            remote_path: Path on remote storage
            local_path: Destination path on local filesystem
            
        Returns:
            BackupResult with operation details
        """
        pass
    
    @abstractmethod
    async def download_bytes(self, remote_path: str) -> tuple[bytes, BackupResult]:
        """
        Download file content as bytes.
        
        Args:
            remote_path: Path on remote storage
            
        Returns:
            Tuple of (file content bytes, BackupResult)
        """
        pass
    
    @abstractmethod
    async def delete(self, remote_path: str) -> bool:
        """
        Delete a file from remote storage.
        
        Args:
            remote_path: Path to file on remote storage
            
        Returns:
            True if deletion successful
        """
        pass
    
    @abstractmethod
    async def exists(self, remote_path: str) -> bool:
        """
        Check if file exists on remote storage.
        
        Args:
            remote_path: Path to check
            
        Returns:
            True if file exists
        """
        pass
    
    @abstractmethod
    async def list_files(self, remote_path: str = "/") -> List[FileInfo]:
        """
        List files in remote directory.
        
        Args:
            remote_path: Directory path to list
            
        Returns:
            List of FileInfo objects
        """
        pass
    
    @abstractmethod
    async def ensure_directory(self, remote_path: str) -> bool:
        """
        Ensure a directory exists on remote storage.
        
        Args:
            remote_path: Directory path to create
            
        Returns:
            True if directory exists or was created
        """
        pass
    
    @abstractmethod
    async def test_connection(self) -> ConnectionTestResult:
        """
        Test connection to remote storage.
        
        Returns:
            ConnectionTestResult with test details
        """
        pass
    
    @property
    @abstractmethod
    def protocol_type(self) -> str:
        """Return the protocol type identifier."""
        pass
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
