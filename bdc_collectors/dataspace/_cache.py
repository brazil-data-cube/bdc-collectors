#
# This file is part of Brazil Data Cube BDC-Collectors.
# Copyright (C) 2023 INPE.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/gpl-3.0.html>.
#

"""Define a minimal cache strategy for Dataspace metadata.

This file contains the following strategies:
- :class:`bdc_collectors.dataspace._cache.RedisStrategy`
- :class:`bdc_collectors.dataspace._cache.RawDictStrategy`
"""

import os
import threading
from abc import ABCMeta

from flask import current_app

try:
    import redis
except ImportError:
    redis = None


class Cache(metaclass=ABCMeta):
    """Simple abstraction of Cache handler."""

    def store(self, key, value, **properties):
        """Store the value into cache.

        Args:
            key(str): Cache key
            value(str): Cache value
            **properties: Extra properties to cache handler
        """
        raise NotImplementedError()

    def get(self, keys):
        """Retrieve the cache information.

        Args:
            keys(str)

        Returns:
            (str) Cache values
        """
        raise NotImplementedError()

    def lock(self, key: str, **kwargs):
        """Retrieve a lock for dealing with cache."""
        raise NotImplementedError()


class RedisStrategy(Cache):
    """Simple implementation of Redis cache as strategy."""

    def __init__(self, redis_url=None):
        """Create a Redis Strategy.

        Args:
            redis_url(str): Redis URL Connection.
        """
        if redis is None:
            raise ImportError("Missing redis library for Redis Cache strategy. Run 'pip install redis'.")

        if redis_url is None:
            redis_url = current_app.config.get('REDIS_URL', os.getenv('REDIS_URL'))

            if redis_url is None:
                raise RuntimeError('Parallel support requires Redis instance. Make sure to export REDIS_URL.')

        self._redis = redis.Redis.from_url(redis_url)
        self._locks = dict()

    def store(self, key, value, **properties):
        """Store the cache values into Redis handler."""
        duration = properties.get('duration', 600)

        self._redis.set(key, value, ex=duration)

    def get(self, key):
        """Retrieve the cache information from Redis handler."""
        try:
            return self._redis.get(key)
        except redis.RedisError:
            # We should notify apm server about cache error
            return None

    def exists(self, key):
        """Check if a key is cached."""
        return self._redis.exists(key)

    def lock(self, key: str, **kwargs):
        """Retrieve a Redis Lock."""
        if key not in self._locks:
            lock = self._redis.lock(key, **kwargs)
            self._redis.expire(key, 30)

            self._locks[key] = lock

        return self._locks[key]


class RawDictStrategy(Cache):
    """Simple implementation of cache as strategy using Python dictionaries."""

    def __init__(self, url=None):
        """Create a In-memory strategy."""
        self._cache = {}
        self._locks = {}

    def store(self, key, value, **properties):
        """Store the cache values into Redis handler."""
        self._cache[key] = value

    def get(self, key):
        """Retrieve the cache information from Redis handler."""
        return self._cache.get(key)

    def exists(self, key):
        """Check if a key is cached."""
        return self._cache.get(key) is not None

    def lock(self, key: str, **kwargs):
        """Retrieve a Redis Lock."""
        if key not in self._locks:
            lock = threading.Lock()

            self._locks[key] = lock

        return self._locks[key]


class CacheService:
    """Base cache service.

    Handle the cache implementations to isolates
    the cache abstraction through libraries.
    """

    def __init__(self, strategy):
        """Create a instance of CacheService.

        Args:
            strategy (Cache): A cache strategy implementation
        """
        if not isinstance(strategy, Cache):
            raise TypeError('Cache strategy must be instance of Cache')

        self._cache = strategy

    def add(self, key, value, duration=None):
        """Store the value into cache handler.

        Args:
            key (str): Cache key
            value (str): Cache value
            duration (int): Time expiration (ms)
        """
        self._cache.store(key, value, duration=duration)

    def get(self, key):
        """Retrieve the cache information.

        Args:
            key (str): Cache key

        Returns:
            str Cache information value
        """
        return self._cache.get(key)

    def exists(self, key: str) -> bool:
        """Check if the key is stored in cache."""
        return self._cache.exists(key)

    def lock(self, key: str, **kwargs):
        """Try to get a lock from the cache system."""
        return self._cache.lock(key, **kwargs)
