#
# This file is part of BDC-Collectors.
# Copyright (C) 2020 INPE.
#
# BDC-Collectors is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Define the base abstractions for BDC-Collectors and Data Collections."""

from datetime import datetime
from pathlib import Path
from typing import Dict, Iterator, List, Tuple, Type

from bdc_catalog.models import Collection
from flask import current_app


class SceneParser:
    """Define the base parser of Scene identifiers."""

    scene_id: str

    def __init__(self, scene_id: str):
        """Create the scene parser."""
        self.scene_id = scene_id

    def tile_id(self) -> str:
        """Retrieve the tile identifier from scene_id."""
        raise NotImplementedError()

    def sensing_date(self) -> datetime:
        """Retrieve the scene sensing date."""
        raise NotImplementedError()

    def processing_date(self) -> datetime:
        """Retrieve the scene processing date."""
        return self.sensing_date()

    def satellite(self) -> str:
        """Retrieve the scene satellite origin."""
        raise NotImplementedError()

    def source(self) -> str:
        """Define meta information for scene_id."""
        raise NotImplementedError()

    def level(self) -> str:
        """Retrieve the collection level."""
        raise NotImplementedError()


class BaseCollection:
    """Define the collection signature of a Provider."""

    parser_class: Type[SceneParser]
    parser: SceneParser
    collection: Collection

    def __init__(self, scene_id: str, collection: Collection = None):
        """Create the data collection definition."""
        self.parser = self.parser_class(scene_id)
        self.collection = collection

    def get_files(self, collection: Collection, path=None, prefix=None) -> Dict[str, Path]:
        """List all files in the collection."""
        if path is None:
            path = self.path(collection, prefix=prefix)

        entries = list(Path(path).rglob(f'*{self.parser.scene_id}*'))

        return {i: entry for i, entry in enumerate(entries)}

    def get_assets(self, collection: Collection, path=None, prefix=None) -> Dict[str, str]:
        """Get a list of extra assets contained in collection path.

        Args:
            collection - A instance of bdc_catalog.models.Collection context.
            path - Path to seek for the files
            prefix - Extra prefix. By default, used the Brazil Data Cube Cluster.

        Returns:
            Dict[str, str]
            Map of asset_name and the absolute asset in disk.
        """
        return dict()

    def path(self, collection: Collection, prefix=None) -> Path:
        """Retrieve the relative path to the Collection on Brazil Data Cube cluster."""
        if prefix is None:
            prefix = current_app.config.get('DATA_DIR')

        sensing_date = self.parser.sensing_date()

        year_month = sensing_date.strftime('%Y-%m')

        scene_path = Path(prefix or '') / 'Repository/Archive' / collection.name / year_month / self.parser.tile_id()

        scene_path = scene_path / self.parser.scene_id

        return scene_path

    def compressed_file(self, collection: Collection, prefix=None) -> Path:
        """Retrieve the path to the compressed file L1.

        TODO: This function will be deprecated in the next release.
              The compressed files will be stored in `.path`.
        """
        raise NotImplementedError()

    def __str__(self):
        """Define data collection string representation."""
        return 'BaseCollection'


class SceneResult(dict):
    """Class structure for Query Scene results."""

    def __init__(self, scene_id, cloud_cover, **kwargs):
        """Create a scene result instance."""
        super().__init__(scene_id=scene_id, cloud_cover=cloud_cover, **kwargs)

    @property
    def scene_id(self) -> str:
        """Retrieve the scene identifier."""
        return self['scene_id']

    @property
    def cloud_cover(self) -> float:
        """Retrieve the  cloud cover metadata."""
        return self['cloud_cover']

    @property
    def link(self) -> str:
        """Retrieve the link of scene id.

        Notes:
            It usually points to download url.
        """
        return self['link']


DownloadResult = List[str]
ScheduledResult = List[str]
FailureResult = List[str]
BulkDownloadResult = Tuple[DownloadResult, ScheduledResult, FailureResult]
"""Type to identify Bulk download result, which represents Success, scheduled (offline) and failure."""
SceneResults = List[SceneResult]


class BaseProvider:
    """Define the signature of a Data Collector Provider."""

    collections: Dict[str, Type[BaseCollection]] = dict()

    def collections_supported(self):
        """Retrieve the collections supported by the Provider instance."""
        return self.collections

    def get_collector(self, collection: str) -> Type[BaseCollection]:
        """Retrieve the data type of the given data collection."""
        return self.collections.get(collection)

    def search(self, query, *args, **kwargs) -> SceneResults:
        """Search for data set in Provider.

        Args:
            query - Data set reference name.
            *args - Optional parameters order for the given provider.
            **kwargs - Optional keywords for given provider, like start_date, end_date and so on.
        """
        raise NotImplementedError()

    def download(self, scene_id: str, *args, **kwargs) -> str:
        """Download the scene from remote provider."""
        raise NotImplementedError()

    def download_all(self, scenes: List[SceneResult], output: str, **kwargs) -> BulkDownloadResult:
        """Bulk download scenes from remote provider."""
        raise NotImplementedError()

    def disconnect(self):
        """Disconnect from Data Provider."""
