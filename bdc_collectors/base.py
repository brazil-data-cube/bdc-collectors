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

"""Define the base abstractions for BDC-Collectors and Data Collections."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple, Type

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
    """Define the collection signature of a Provider.

    A collection essentially represents an Item briefing, in other words,
    a path to the scene identifier.
    Each collection item has custom path resolver which is resolved by
    :func:`~bdc_collectors.base.BaseCollection.path`. You may implement
    this method in your impl class for custom directory location.
    """

    parser_class: Type[SceneParser]
    parser: SceneParser
    collection: Any

    def __init__(self, scene_id: str, collection=None):
        """Create the data collection definition."""
        self.parser = self.parser_class(scene_id)
        self.collection = collection

    def get_files(self, collection, path=None, prefix=None, **kwargs) -> Dict[str, Path]:
        """List all files in the collection.

        Returns:
            Dict[str,Path]
                Map of found files in resolved path location.
        """
        if path is None:
            path = self.path(collection, prefix=prefix)

        entries = list(Path(path).rglob(f'*{self.parser.scene_id}*'))

        return {i: entry for i, entry in enumerate(entries)}

    def get_assets(self, collection, path=None, prefix=None, **kwargs) -> Dict[str, str]:
        """Get a list of extra assets contained in collection path.

        Args:
            collection: A instance of bdc_catalog.models.Collection context.
            path (Path): Path to seek for the files. Default is ``None``.
            prefix (str): Extra prefix. By default, used the Brazil Data Cube Cluster.

        Returns:
            Dict[str, str]
                Map of ``asset_name`` and the ``absolute asset`` in disk.
        """
        return dict()

    def path(self, collection, prefix=None, path_include_month=False, **kwargs) -> Path:
        """Retrieve the relative path to the Collection on Brazil Data Cube cluster.

        Note:
            When prefix is not set, this func tries to get value from env ``DATA_DIR``.

        Args:
            collection: Instance of BDC Collection model
            prefix (str): Path prefix
        """
        if prefix is None:
            prefix = current_app.config.get('DATA_DIR')

        sensing_date = self.parser.sensing_date()

        year_month = sensing_date.strftime('%Y-%m')

        scene_path = Path(prefix or '') / collection.name / year_month / self.parser.tile_id()

        scene_path = scene_path / self.parser.scene_id

        return scene_path

    def compressed_file(self, collection, prefix=None, path_include_month=False, **kwargs) -> Path:
        """Retrieve the path to the compressed file L1.

        .. deprecated:: 0.6.2
            This function will be deprecated in the next release.
            Use :func:`~bdc_collectors.base.BaseCollection.path` instead with own extension method.
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

        Note:
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
        """Retrieve the collections supported by the Provider instance.

        Returns:
            Dict[str, Type[BaseCollection]]
                List of Well-known collection in ``Provider``.
        """
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
