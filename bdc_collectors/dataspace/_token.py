#
# This file is part of Brazil Data Cube BDC-Collectors.
# Copyright (C) 2022 INPE.
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

"""Describe Abstraction for Sentinel Data Space EcoSystem on Copernicus."""

import json
import random
import time
import typing as t

from ..utils import import_entry
from ._cache import Cache, CacheService, RawDictStrategy
from .utils import AccessToken, get_access_token


class TokenManager:
    """Global user client for Sentinel Accounts.
    
    This class stores the access tokens in memory using a cache method: Redis or Python Dict.
    Whenever a token is about to expire, this class automatically asks for a new token in
    DataSpace authorization server.
    
    Examples:
        Use the TokenManager as following to generate a new token:    

        >>> from bdc_collectors.dataspace._token import TokenManager
        >>> manager = TokenManager("username", "password")
        >>> token = manager.get_token()
        >>> # Use the token to download anything during the next 10 minutes
        >>> another = manager.get_token()

        You can also use Redis Backend for token management. (Make sure you have the library 'redis' installed and server up and running.)

        >>> from bdc_collectors.dataspace._cache import RedisStrategy
        >>> from bdc_collectors.dataspace._token import TokenManager
        >>> manager = TokenManager("username", "password", token_cache=RedisStrategy())
        >>> token = manager.get_token()
    """

    def __init__(self, username: str, password: str,
                 token_lock_name='dataspace-tokens',
                 token_cache: t.Optional[t.Union[str, Cache]] = None,
                 token_limit: int = 2, **kwargs):
        """Build user clients interface."""
        self._username = username
        self._password = password

        self._key = 'dataspace:tokens'
        self._limit = token_limit

        if token_cache is None:
            token_cache = RawDictStrategy()
        elif isinstance(token_cache, str):
            strategy_cls: t.Type[Cache] = import_entry(token_cache)
            token_cache = strategy_cls(**kwargs)

        self._cache = CacheService(token_cache)

        self._lock = self._cache.lock(token_lock_name)

    @property
    def tokens(self) -> t.List[AccessToken]:
        """Retrieve all users from disk."""
        data = self._cache.get(self._key)
        cached_tokens = json.loads(data) if data else []
        return [AccessToken(**token) for token in cached_tokens]

    @tokens.setter
    def tokens(self, obj):
        """Update users."""
        self._cache.add(self._key, json.dumps(obj))

    def use(self):
        """Try to lock an atomic user."""
        with self._lock:
            cached_tokens = self.tokens
            tokens: t.List[AccessToken] = []

            if len(cached_tokens) < self._limit:
                missing = self._limit - len(cached_tokens)
                for _ in range(missing):
                    token = get_access_token(self._username, self._password)
                    time.sleep(1)
                    tokens.append(token)

            for token in cached_tokens:
                if token.expired():
                    token = get_access_token(self._username, self._password) # token.refresh()

                tokens.append(token)

            self.tokens = tokens

            return random.choice(tokens)

    def get_token(self):
        """Try to get available user to download."""
        token = self.use()

        return token
