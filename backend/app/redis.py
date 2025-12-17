from typing import Optional
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

redis_client = None


class FakeRedis:
    """A simple in-memory fake Redis for development without Redis server."""
    
    # 最大存储条目数，防止内存泄漏
    MAX_ENTRIES = 10000
    # 清理阈值
    CLEANUP_THRESHOLD = 8000
    
    def __init__(self):
        self._data = {}
        self._expiry = {}
        self._access_order = []  # LRU tracking
    
    def _check_expiry(self, key: str) -> bool:
        """Check if key has expired. Returns True if key is valid."""
        import time
        if key in self._expiry:
            if time.time() > self._expiry[key]:
                # Key has expired, remove it
                self._data.pop(key, None)
                self._expiry.pop(key, None)
                if key in self._access_order:
                    self._access_order.remove(key)
                return False
        return key in self._data
    
    def _cleanup_expired(self):
        """Clean up all expired keys."""
        import time
        current_time = time.time()
        expired_keys = [k for k, v in self._expiry.items() if current_time > v]
        for key in expired_keys:
            self._data.pop(key, None)
            self._expiry.pop(key, None)
            if key in self._access_order:
                self._access_order.remove(key)
    
    def _enforce_max_entries(self):
        """Enforce maximum entries limit using LRU eviction."""
        if len(self._data) > self.CLEANUP_THRESHOLD:
            # First, clean up expired entries
            self._cleanup_expired()
            
            # If still over limit, evict oldest entries
            while len(self._data) > self.CLEANUP_THRESHOLD and self._access_order:
                oldest_key = self._access_order.pop(0)
                self._data.pop(oldest_key, None)
                self._expiry.pop(oldest_key, None)
    
    def _touch(self, key: str):
        """Update access order for LRU."""
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)
    
    async def get(self, key: str) -> Optional[str]:
        self._check_expiry(key)
        if key in self._data:
            self._touch(key)
            return self._data.get(key)
        return None
    
    async def set(self, key: str, value: str, ex: int = None):
        import time
        self._enforce_max_entries()
        self._data[key] = value
        self._touch(key)
        if ex:
            self._expiry[key] = time.time() + ex
        return True
    
    async def setex(self, key: str, seconds: int, value: str):
        import time
        self._enforce_max_entries()
        self._data[key] = value
        self._touch(key)
        self._expiry[key] = time.time() + seconds
        return True
    
    async def incr(self, key: str):
        self._check_expiry(key)
        self._enforce_max_entries()
        val = int(self._data.get(key, 0)) + 1
        self._data[key] = str(val)
        self._touch(key)
        return val
    
    async def expire(self, key: str, seconds: int):
        import time
        if key in self._data:
            self._expiry[key] = time.time() + seconds
        return True
    
    async def delete(self, key: str):
        self._data.pop(key, None)
        self._expiry.pop(key, None)
        if key in self._access_order:
            self._access_order.remove(key)
        return 1
    
    async def exists(self, key: str):
        self._check_expiry(key)
        return 1 if key in self._data else 0
    
    def pipeline(self):
        return FakePipeline(self)
    
    async def close(self):
        pass


class FakePipeline:
    def __init__(self, redis_instance):
        self._redis = redis_instance
        self._commands = []
    
    def incr(self, key: str):
        self._commands.append(('incr', key))
        return self
    
    def expire(self, key: str, seconds: int):
        self._commands.append(('expire', key, seconds))
        return self
    
    async def execute(self):
        import time
        results = []
        self._redis._enforce_max_entries()
        for cmd in self._commands:
            if cmd[0] == 'incr':
                self._redis._check_expiry(cmd[1])
                val = int(self._redis._data.get(cmd[1], 0)) + 1
                self._redis._data[cmd[1]] = str(val)
                self._redis._touch(cmd[1])
                results.append(val)
            elif cmd[0] == 'expire':
                if cmd[1] in self._redis._data:
                    self._redis._expiry[cmd[1]] = time.time() + cmd[2]
                results.append(True)
        return results


async def init_redis():
    global redis_client
    
    if settings.redis_enabled and settings.redis_url:
        try:
            import redis.asyncio as redis
            redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            await redis_client.ping()
            logger.info("Connected to Redis server")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}, using fake Redis")
            redis_client = FakeRedis()
    else:
        logger.info("Redis disabled, using in-memory fake Redis")
        redis_client = FakeRedis()
    
    return redis_client


async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.close()


def get_redis():
    return redis_client
