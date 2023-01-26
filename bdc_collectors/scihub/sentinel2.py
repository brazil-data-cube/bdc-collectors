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

from .base import SentinelCollection
from .parser import Sentinel1Scene


class Sentinel1(SentinelCollection):
    """Simple abstraction for Sentinel-1."""

    parser_class = Sentinel1Scene

    def path(self, collection, prefix=None) -> Path:
        if prefix is None:
            prefix = current_app.config.get('DATA_DIR')

        date = self.parser.sensing_date()
        year = str(date.year)
        month = date.strftime('%MM')
        relative = f'{collection.name}/v{collection.version}/{year}/{month}/{self.parser.scene_id}'

        return Path(prefix or '') / relative

    def get_files(self, collection, path=None, prefix=None):
        globber = Path(path or self.path(collection, prefix)).rglob('*')
        output = {}
        for entry in globber:
            if entry.suffix.lower() == '.tif':
                name = '_'.join(entry.stem.split('_')[-2:])
                output[name] = entry
        return output


class Sentinel2(SentinelCollection):
    """Simple abstraction for Sentinel-2."""
