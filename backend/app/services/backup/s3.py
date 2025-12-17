"""
Unified S3-Compatible Backup Backend

Supports all S3-compatible object storage services:
- AWS S3
- Cloudflare R2
- Tencent Cloud COS (S3 mode)
- MinIO
- Backblaze B2
- DigitalOcean Spaces
- Aliyun OSS (S3 mode)
- Any other S3-compatible service

Reuses the same configuration patterns as the storage module.
"""
import os
import time
import hashlib
import asyncio
from typing import List, Optional
from datetime import datetime

import aioboto3
from botocore.config import Config

from app.services.backup.base import (
    BackupBackend, BackupResult, FileInfo, ConnectionTestResult
)


# Provider presets for common S3-compatible services
S3_PROVIDER_PRESETS = {
    'aws': {
        'name': 'AWS S3',
        'endpoint_pattern': None,  # Uses default AWS endpoint
        'region_required': True,
        'path_style': False,
        'default_region': 'us-east-1',
    },
    'r2': {
        'name': 'Cloudflare R2',
        'endpoint_pattern': 'https://{account_id}.r2.cloudflarestorage.com',
        'region_required': False,
        'path_style': True,
        'default_region': 'auto',
    },
    'cos': {
        'name': 'Tencent Cloud COS',
        'endpoint_pattern': 'https://cos.{region}.myqcloud.com',
        'region_required': True,
        'path_style': False,
        'default_region': 'ap-guangzhou',
    },
    'oss': {
        'name': 'Aliyun OSS',
        'endpoint_pattern': 'https://oss-{region}.aliyuncs.com',
        'region_required': True,
        'path_style': False,
        'default_region': 'cn-hangzhou',
    },
    'minio': {
        'name': 'MinIO',
        'endpoint_pattern': None,  # User provides full endpoint
        'region_required': False,
        'path_style': True,
        'default_region': 'us-east-1',
    },
    'b2': {
        'name': 'Backblaze B2',
        'endpoint_pattern': 'https://s3.{region}.backblazeb2.com',
        'region_required': True,
        'path_style': False,
        'default_region': 'us-west-002',
    },
    'spaces': {
        'name': 'DigitalOcean Spaces',
        'endpoint_pattern': 'https://{region}.digitaloceanspaces.com',
        'region_required': True,
        'path_style': False,
        'default_region': 'nyc3',
    },
    'custom': {
        'name': 'Custom S3-Compatible',
        'endpoint_pattern': None,
        'region_required': False,
        'path_style': None,  # Auto-detect
        'default_region': 'us-east-1',
    },
}


class S3BackupBackend(BackupBackend):
    """Unified S3-compatible backup backend using aioboto3."""
    
    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        region: Optional[str] = None,
        prefix: str = "",
        provider: str = "custom",
        path_style: Optional[bool] = None,
    ):
        """
        Initialize S3-compatible backup backend.
        
        Args:
            endpoint: S3 endpoint URL (e.g., https://s3.amazonaws.com)
            access_key: Access Key ID
            secret_key: Secret Access Key
            bucket_name: Bucket name
            region: Region name (use 'auto' for R2)
            prefix: Path prefix for all files
            provider: Provider preset (aws, r2, cos, oss, minio, b2, spaces, custom)
            path_style: Use path-style addressing (auto-detect if None)
        """
        self.provider = provider or 'custom'
        preset = S3_PROVIDER_PRESETS.get(self.provider, S3_PROVIDER_PRESETS['custom'])
        
        self.endpoint = endpoint.rstrip('/') if endpoint else None
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket_name = bucket_name
        self.region = region or preset.get('default_region', 'us-east-1')
        self.prefix = prefix.strip("/") if prefix else ""
        
        # Determine path style
        if path_style is not None:
            self._path_style = path_style
        elif preset.get('path_style') is not None:
            self._path_style = preset['path_style']
        else:
            # Auto-detect based on endpoint
            self._path_style = self._detect_path_style(self.endpoint)
        
        self._session = None
    
    def _detect_path_style(self, endpoint: str) -> bool:
        """Auto-detect if path-style addressing should be used."""
        if not endpoint:
            return False
        
        path_style_indicators = [
            'r2.cloudflarestorage',
            'minio',
            ':9000',
            ':9001',
            'localhost',
            '127.0.0.1',
        ]
        
        endpoint_lower = endpoint.lower()
        return any(indicator in endpoint_lower for indicator in path_style_indicators)
    
    @property
    def protocol_type(self) -> str:
        return "s3"
    
    async def connect(self) -> bool:
        """Initialize S3 session."""
        try:
            self._session = aioboto3.Session()
            return True
        except Exception as e:
            raise ConnectionError(f"S3 session initialization failed: {str(e)}")
    
    async def disconnect(self) -> None:
        """Close S3 session."""
        self._session = None
    
    def _get_full_key(self, remote_path: str) -> str:
        """Get full S3 key including prefix."""
        path = remote_path.lstrip("/")
        if self.prefix:
            return f"{self.prefix}/{path}"
        return path
    
    async def _get_client(self):
        """Get S3 client context manager."""
        if not self._session:
            await self.connect()
        
        # Build config with path style if needed
        config_kwargs = {
            'signature_version': 's3v4',
            'retries': {'max_attempts': 3, 'mode': 'adaptive'},
            'connect_timeout': 30,
            'read_timeout': 60,
        }
        
        if self._path_style:
            config_kwargs['s3'] = {'addressing_style': 'path'}
        
        client_kwargs = {
            'aws_access_key_id': self.access_key,
            'aws_secret_access_key': self.secret_key,
            'region_name': self.region,
            'config': Config(**config_kwargs),
        }
        
        if self.endpoint:
            client_kwargs['endpoint_url'] = self.endpoint
            # Disable SSL verification for self-signed certificates
            client_kwargs['verify'] = not any(x in self.endpoint.lower() for x in ['localhost', '127.0.0.1', ':9000'])
        
        return self._session.client('s3', **client_kwargs)
    
    async def upload(self, local_path: str, remote_path: str) -> BackupResult:
        """Upload a file to S3."""
        key = self._get_full_key(remote_path)
        filename = os.path.basename(local_path)
        
        try:
            # Read file and calculate checksum
            with open(local_path, "rb") as f:
                content = f.read()
            
            checksum = hashlib.md5(content).hexdigest()
            
            # Determine content type
            ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
            content_types = {
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'png': 'image/png',
                'gif': 'image/gif',
                'webp': 'image/webp',
                'svg': 'image/svg+xml',
                'ico': 'image/x-icon',
            }
            content_type = content_types.get(ext, 'application/octet-stream')
            
            async with await self._get_client() as client:
                await client.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=content,
                    ContentType=content_type,
                )
            
            return BackupResult(
                success=True,
                filename=filename,
                bytes_transferred=len(content),
                remote_path=key,
                checksum=checksum,
            )
        except Exception as e:
            return BackupResult(
                success=False,
                filename=filename,
                error_message=str(e),
            )
    
    async def upload_bytes(self, content: bytes, remote_path: str) -> BackupResult:
        """Upload bytes directly to S3."""
        key = self._get_full_key(remote_path)
        filename = os.path.basename(remote_path)
        
        try:
            checksum = hashlib.md5(content).hexdigest()
            
            async with await self._get_client() as client:
                await client.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=content,
                )
            
            return BackupResult(
                success=True,
                filename=filename,
                bytes_transferred=len(content),
                remote_path=key,
                checksum=checksum,
            )
        except Exception as e:
            return BackupResult(
                success=False,
                filename=filename,
                error_message=str(e),
            )
    
    async def download(self, remote_path: str, local_path: str) -> BackupResult:
        """Download a file from S3."""
        key = self._get_full_key(remote_path)
        filename = os.path.basename(remote_path)
        
        try:
            # Ensure local directory exists
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            async with await self._get_client() as client:
                response = await client.get_object(
                    Bucket=self.bucket_name,
                    Key=key,
                )
                content = await response["Body"].read()
            
            # Write to local file
            with open(local_path, "wb") as f:
                f.write(content)
            
            checksum = hashlib.md5(content).hexdigest()
            
            return BackupResult(
                success=True,
                filename=filename,
                bytes_transferred=len(content),
                remote_path=key,
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
        key = self._get_full_key(remote_path)
        filename = os.path.basename(remote_path)
        
        try:
            async with await self._get_client() as client:
                response = await client.get_object(
                    Bucket=self.bucket_name,
                    Key=key,
                )
                content = await response["Body"].read()
            
            checksum = hashlib.md5(content).hexdigest()
            
            result = BackupResult(
                success=True,
                filename=filename,
                bytes_transferred=len(content),
                remote_path=key,
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
        """Delete a file from S3."""
        key = self._get_full_key(remote_path)
        try:
            async with await self._get_client() as client:
                await client.delete_object(
                    Bucket=self.bucket_name,
                    Key=key,
                )
            return True
        except Exception:
            return False
    
    async def exists(self, remote_path: str) -> bool:
        """Check if file exists in S3."""
        key = self._get_full_key(remote_path)
        try:
            async with await self._get_client() as client:
                await client.head_object(
                    Bucket=self.bucket_name,
                    Key=key,
                )
            return True
        except Exception:
            return False
    
    async def list_files(self, remote_path: str = "/") -> List[FileInfo]:
        """List files in S3 bucket with prefix."""
        prefix = self._get_full_key(remote_path)
        if prefix and not prefix.endswith("/"):
            prefix += "/"
        
        files = []
        
        try:
            async with await self._get_client() as client:
                paginator = client.get_paginator("list_objects_v2")
                async for page in paginator.paginate(
                    Bucket=self.bucket_name,
                    Prefix=prefix,
                    Delimiter="/",
                ):
                    # Add files
                    for obj in page.get("Contents", []):
                        key = obj["Key"]
                        filename = key.split("/")[-1]
                        if filename:  # Skip empty names (directories)
                            files.append(FileInfo(
                                filename=filename,
                                size=obj["Size"],
                                modified_time=obj["LastModified"],
                                is_directory=False,
                            ))
                    
                    # Add directories
                    for prefix_obj in page.get("CommonPrefixes", []):
                        dir_name = prefix_obj["Prefix"].rstrip("/").split("/")[-1]
                        files.append(FileInfo(
                            filename=dir_name,
                            size=0,
                            is_directory=True,
                        ))
        except Exception:
            pass
        
        return files
    
    async def ensure_directory(self, remote_path: str) -> bool:
        """S3 doesn't need explicit directory creation."""
        return True
    
    async def test_connection(self) -> ConnectionTestResult:
        """Test S3 connection."""
        start_time = time.time()
        
        try:
            async with await self._get_client() as client:
                # Try to list bucket (head_bucket) with timeout
                await asyncio.wait_for(
                    client.head_bucket(Bucket=self.bucket_name),
                    timeout=30.0
                )
            
            latency = (time.time() - start_time) * 1000
            
            # Get provider display name
            preset = S3_PROVIDER_PRESETS.get(self.provider, S3_PROVIDER_PRESETS['custom'])
            provider_name = preset.get('name', 'S3-Compatible')
            
            return ConnectionTestResult(
                success=True,
                message=f"{provider_name} 连接成功",
                latency_ms=latency,
                details={
                    "provider": self.provider,
                    "provider_name": provider_name,
                    "endpoint": self.endpoint,
                    "bucket": self.bucket_name,
                    "region": self.region,
                    "path_style": self._path_style,
                }
            )
        except asyncio.TimeoutError:
            return ConnectionTestResult(
                success=False,
                message=f"S3 连接超时: {self.endpoint}",
                latency_ms=None,
                details={
                    "provider": self.provider,
                    "endpoint": self.endpoint,
                    "bucket": self.bucket_name,
                    "error": "Connection timeout",
                }
            )
        except Exception as e:
            error_msg = str(e)
            
            # Provide more specific error messages
            if "InvalidAccessKeyId" in error_msg or "SignatureDoesNotMatch" in error_msg:
                return ConnectionTestResult(
                    success=False,
                    message="S3 认证失败 - 请检查 Access Key 和 Secret Key",
                    latency_ms=None,
                    details={
                        "provider": self.provider,
                        "endpoint": self.endpoint,
                        "bucket": self.bucket_name,
                        "error": "Invalid credentials",
                    }
                )
            elif "NoSuchBucket" in error_msg:
                return ConnectionTestResult(
                    success=False,
                    message=f"存储桶 '{self.bucket_name}' 不存在",
                    latency_ms=None,
                    details={
                        "provider": self.provider,
                        "endpoint": self.endpoint,
                        "bucket": self.bucket_name,
                        "error": "Bucket does not exist",
                    }
                )
            elif "AccessDenied" in error_msg:
                return ConnectionTestResult(
                    success=False,
                    message=f"访问被拒绝 - 请检查存储桶权限",
                    latency_ms=None,
                    details={
                        "provider": self.provider,
                        "endpoint": self.endpoint,
                        "bucket": self.bucket_name,
                        "error": "Access denied",
                    }
                )
            else:
                return ConnectionTestResult(
                    success=False,
                    message=f"S3 连接失败: {error_msg}",
                    latency_ms=None,
                    details={
                        "provider": self.provider,
                        "endpoint": self.endpoint,
                        "bucket": self.bucket_name,
                        "error": error_msg,
                    }
                )
