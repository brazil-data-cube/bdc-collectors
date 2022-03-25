#
# This file is part of BDC-Collectors.
# Copyright (C) 2020 INPE.
#
# BDC-Collectors is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Define the BDC-Collector flask extension."""

import logging
import warnings
from threading import Lock
from typing import Any, Dict, List, Type

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


class DataCollector:
    """Data wrapper to store the given instance `bdc_catalog.models.Provider` and the data collector factory."""

    _db_provider: Any
    _provider: BaseProvider
    _collection_provider: Any

    def __init__(self, instance, provider: Type[BaseProvider], collection_provider: Any, **kwargs):
        """Create a data collector instance."""
        self._db_provider = instance

        if isinstance(instance.credentials, dict):
            copy_args = instance.credentials.copy()
            copy_args.update(**kwargs)

            self._provider = provider(**copy_args)
        else:
            self._provider = provider(*instance.credentials, **kwargs)

        self._collection_provider = collection_provider

    def __str__(self):
        """Retrieve String representation for DataCollector."""
        return f'DataCollector({self.provider_name})'

    @property
    def active(self) -> bool:
        """Retrieve the provider availability in database."""
        return self._collection_provider.active

    @property
    def priority(self) -> bool:
        """Retrieve the provider priority order in database."""
        return self._collection_provider.priority

    @property
    def instance(self):
        """Retrieve the database instance of bdc_catalog.models.Provider."""
        return self._db_provider

    @property
    def provider_name(self) -> str:
        """Retrieve the provider name."""
        return self._db_provider.name

    def download(self, *args, **kwargs):
        """Download data from remote provider."""
        return self._provider.download(*args, **kwargs)

    def search(self, *args, **kwargs):
        """Search for dataset in the provider."""
        # TODO: Apply adapter in the results here??
        return self._provider.search(*args, **kwargs)


class CollectorExtension:
    """Define the flask extension of BDC-Collectors.

    You can initialize this extension as following::

        app = Flask(__name__)
        ext = CollectorExtension(app)

    This extension use the `Python Entry points specification <https://packaging.python.org/specifications/entry-points/>`_
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

        ext = current_app.extensions['bdc:collector']

        ext.get_provider('providerName')

    Note:
        Make sure to initialize the CollectorExtension before.

    We also the a command line `bdc-collectors` which provides a way to
    consume those providers in terminal::

        bdc-collectors --help
    """

    state: CollectorState

    def __init__(self, app: Flask, **kwargs):
        """Create a instance of extension."""
        self.state = CollectorState()

        if app:
            self.init_app(app, **kwargs)

    def init_app(self, app: Flask, **kwargs):
        """Initialize the BDC-Collector extension, loading supported providers dynamically."""
        from .cli import cli

        extension_name = 'bdc:collector'

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

                if hasattr(provider, 'init_provider') and \
                    callable(provider.init_provider):
                    entry = provider.init_provider()

                    for provider_name, provider in entry.items():
                        self.state.add_provider(provider_name, provider)

    def get_provider(self, provider: str) -> Type[BaseProvider]:
        """Retrieve a provider class."""
        return self.state.get_provider(provider)

    def get_provider_order(self, collection: Any, include_inactive=False, **kwargs) -> List[DataCollector]:
        """Retrieve a list of providers which the bdc_catalog.models.Collection is associated.

        Note:
            This method requires the initialization of extension `bdc_catalog.ext.BDCCatalog`.

        With a given collection, it seeks in `bdc_catalog.models.Provider`
        and `bdc_catalog.models.CollectionsProviders` association and then
        look for provider supported in the entry point `bdc_collectors.providers`.

        Args:
            collection - An instance of bdc_catalog.models.Collection
            include_inactive - List also the inactive providers. Default=False
            **kwargs - Extra parameters to pass to the Provider instance.

        Returns:
            A list of DataCollector, ordered by priority.
        """
        from bdc_catalog.models import CollectionsProviders, Provider, db
        where = []

        if not include_inactive:
            where.append(CollectionsProviders.active.is_(True))

        collection_providers = db.session\
            .query(Provider, CollectionsProviders) \
            .filter(
                CollectionsProviders.collection_id == collection.id,
                Provider.id == CollectionsProviders.provider_id,
                *where
            ) \
            .order_by(CollectionsProviders.priority.asc()) \
            .all()

        result = []

        for collection_provider in collection_providers:
            provider_name = collection_provider.Provider.name

            provider_class = self.state.get_provider(provider_name)

            if provider_class is None:
                logging.warning(f'The collection requires the provider {provider_name} but it is not supported.')
                continue

            result.append(DataCollector(collection_provider.Provider, provider_class, collection_provider, **kwargs))

        return result

    def list_providers(self) -> List[str]:
        """Retrieve a list of supported providers."""
        return list(self.state.providers.keys())
