#
# This file is part of BDC-Collectors.
# Copyright (C) 2020 INPE.
#
# BDC-Collectors is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Describe Abstraction for Sentinel Data Access on Copernicus."""

import json
import logging
import os
import time
from typing import List

from flask import current_app


class AtomicUser:
    """An abstraction of Atomic User. You must use it as context manager.

    Make sure to control the access to the shared resource.

    Whenever an instance object out of scope, it automatically releases the user to the
    Redis cache.
    """

    def __init__(self, username, password, ref):
        """Build an atomic user."""
        self.username = username
        self.password = password
        self._released = False
        self.ref = ref

    def __repr__(self):
        """Retrieve string representation of Atomic User."""
        return 'AtomicUser({}, released={})'.format(self.username, self._released)

    def __enter__(self):
        """Open atomic user context."""
        return self

    def __del__(self):
        """Release atomic user from copernicus."""
        self.release()

    def release(self):
        """Release atomic user from redis."""
        if not self._released:
            logging.debug('Release {}'.format(self.username))
            self.ref.done(self.username)

            self._released = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context. Release the user from redis client."""
        self.release()


class UserClients:
    """Global user client for Sentinel Accounts."""

    def __init__(self, users: List[dict], redis_url=None, lock_name='user-clients', limit: int = 2):
        """Build user clients interface."""
        import redis

        for user in users:
            user['count'] = 0

        self._key = 'bdc_collection_builder:users'
        self._limit = limit

        if redis_url is None:
            redis_url = current_app.config.get('REDIS_URL', os.getenv('REDIS_URL'))

            if redis_url is None:
                raise RuntimeError('Parallel support requires Redis instance. Make sure to export REDIS_URL.')

        self._cache = redis.Redis.from_url(redis_url)
        self._lock = self._cache.lock(lock_name)
        self.users = users

    @property
    def users(self):
        """Retrieve all users from disk."""
        return json.loads(self._cache.get(self._key))

    @users.setter
    def users(self, obj):
        """Update users."""
        self._cache.set(self._key, json.dumps(obj))

    def use(self):
        """Try to lock an atomic user."""
        with self._lock:
            users = self.users

            for user in users:
                if user['count'] < self._limit:
                    logging.debug('User {} - {}'.format(user['username'], user['count']))
                    user['count'] += 1

                    self.users = users

                    return AtomicUser(user['username'], user['password'], self)
            return None

    def done(self, username):
        """Release atomic user."""
        with self._lock:
            users = self.users

            for user in users:
                if user['username'] == username:
                    user['count'] -= 1

            self.users = users

    def get_user(self):
        """Try to get available user to download."""
        user = None

        while user is None:
            user = self.use()

            if user is None:
                logging.info('Waiting for available user to download...')
                time.sleep(5)

        return user
