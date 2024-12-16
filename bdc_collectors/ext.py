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

"""Define the BDC-Collector flask extension."""

import warnings
from threading import Lock
from typing import Dict, List, Type

import pkg_resources
from flask import Flask

from .base import BaseProvider


class CollectorState:
    """Class for holding Collector state of the extension."""

    providers: Dict[str, Type[BaseProvider]]

    lock: Lock = Lock()

    def __init__(self):
        """Create the state."""
        self.providers = dict()

    def add_provider(self, provider_name: str, provider: Type[BaseProvider]):
        """Add a new provider to supports."""
        with self.lock:
            assert provider_name not in self.providers

            self.providers[provider_name] = provider

    def get_provider(self, provider: str) -> Type[BaseProvider]:
        """Try to retrieve the data provider type."""
        with self.lock:
            if provider in self.providers:
                return self.providers[provider]


class CollectorExtension:
    """Define the flask extension of BDC-Collectors.

    You can initialize this extension as following::

        app = Flask(__name__)
        ext = CollectorExtension(app)

    This extension use the
    `Python Entry points specification <https://packaging.python.org/specifications/entry-points/>`_
    for load data providers dynamically.
    By default, we use the entrypoint `bdc_collectors.providers` as defined in `setup.py`::

        entry_points={
            'bdc_collectors.providers': [
                'google = bdc_collectors.google',
                'usgs = bdc_collectors.usgs',
                'onda = bdc_collectors.onda',
                'scihub = bdc_collectors.scihub'
            ],
        },

    Each provider is hold in the property `state` and may be accessed using::

        from flask import current_app

        ext = current_app.extensions['bdc_collector']

        ext.get_provider('providerName')

    Note:
        Make sure to initialize the ``CollectorExtension`` before.

    We also the command line `bdc-collector` which provides a way to
    consume those providers in terminal::

        bdc-collector --help
    """

    state: CollectorState

    def __init__(self, app: Flask, **kwargs):
        """Create an instance of extension."""
        self.state = CollectorState()

        if app:
            self.init_app(app, **kwargs)

    def init_app(self, app: Flask, **kwargs):
        """Initialize the BDC-Collector extension, loading supported providers dynamically."""
        from .cli import cli

        extension_name = 'bdc_collector'

        if extension_name in app.extensions:
            warnings.warn(f'The module {extension_name} was already initialized before.')
            return

        self.init_providers(**kwargs)

        app.extensions[extension_name] = self
        app.cli.add_command(cli, 'bdc-collector')

    def init_providers(self, entry_point: str = 'bdc_collectors.providers', **kwargs):
        """Load the supported providers from setup.py entry_point."""
        if entry_point:
            for base_entry in pkg_resources.iter_entry_points(entry_point):
                provider = base_entry.load()

                if hasattr(provider, 'init_provider') and callable(provider.init_provider):
                    entry = provider.init_provider()

                    for provider_name, provider in entry.items():
                        self.state.add_provider(provider_name, provider)

    def get_provider(self, provider: str) -> Type[BaseProvider]:
        """Retrieve a provider class loaded in module."""
        return self.state.get_provider(provider)

    def list_providers(self) -> List[str]:
        """Retrieve a list of supported providers."""
        return list(self.state.providers.keys())
