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

"""Defines the structure for Collections on remote SciHub server."""
from pathlib import Path

from flask import current_app

from ..utils import entry_version
from .base import SentinelCollection
from .parser import Sentinel1Scene, Sentinel3Scene


class Sentinel1(SentinelCollection):
    """Simple abstraction for Sentinel-1."""

    parser_class = Sentinel1Scene

    def path(self, collection, prefix=None, path_include_month=False) -> Path:
        if prefix is None:
            prefix = current_app.config.get('DATA_DIR')

        date = self.parser.sensing_date()
        year = str(date.year)
        day = str(date.day)
        month = date.strftime('%MM')
        version = entry_version(collection.version)
        relative = f'{collection.name}/{version}/{year}/{month}/{day}'

        return Path(prefix or '') / relative

    def get_files(self, collection, path=None, prefix=None):
        globber = Path(path or self.path(collection, prefix)).rglob('*')
        output = {}
        for entry in globber:
            if entry.suffix.lower() == '.tif':
                name = '_'.join(entry.stem.split('_')[-2:])
                output[name] = entry
        return output

    def compressed_file(self, collection, prefix=None, path_include_month=False):
        """Retrieve path to the compressed scene (.zip) on local storage."""
        if prefix is None:
            prefix = current_app.config.get('DATA_DIR')

        scene_id = self.parser.scene_id
        scene_path = self.path(collection, prefix=prefix, path_include_month=path_include_month)

        return scene_path / f'{scene_id}.zip'


class Sentinel2(SentinelCollection):
    """Simple abstraction for Sentinel-2."""


class Sentinel3(SentinelCollection):
    """Simple abstraction for Sentinel-3."""

    parser_class = Sentinel3Scene

    def get_files(self, collection, path=None, prefix=None):
        """List all files in the collection."""
        if path is None:
            path = self.path(collection, prefix)

        path = Path(path)

        output = dict()

        for entry in path.rglob("*.nc"):
            output[entry.stem] = entry

        return output

    def compressed_file(self, collection, prefix=None, path_include_month=False):
        """Retrieve path to the compressed scene (.zip) on local storage."""
        if prefix is None:
            prefix = current_app.config.get('DATA_DIR')

        scene_id = self.parser.scene_id
        scene_path = self.path(collection, prefix=prefix, path_include_month=path_include_month)

        return scene_path / f'{scene_id}.zip'

    def path(self, collection, prefix=None, path_include_month=False) -> Path:
        """Retrieve the relative path to the Collection on Brazil Data Cube cluster."""
        if prefix is None:
            prefix = current_app.config.get('DATA_DIR')

        year = str(self.parser.sensing_date().year)
        month = str(self.parser.sensing_date().month)
        day = str(self.parser.sensing_date().day)
        version = entry_version(collection.version)

        relative = Path(collection.name) / version / year / month / day

        scene_path = Path(prefix or '') / relative

        return scene_path

    def get_assets(self, collection, path=None, prefix=None) -> dict:
        """Retrieve the map assets of Sentinel product."""
        if path is None:
            path = self.path(collection, prefix=prefix)

        path = Path(path)

        output = dict()

        thumbnail = list(path.rglob('*.jpg'))

        if thumbnail:
            output['thumbnail'] = str(thumbnail)

        return output