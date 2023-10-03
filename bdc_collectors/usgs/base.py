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

"""Base definitions for USGS catalog."""

from pathlib import Path

from flask import current_app

from ..base import BaseCollection
from ..utils import entry_version
from .parser import LandsatScene


class USGSCollection(BaseCollection):
    """Define a generic way to deal with USGS collections."""

    def _path(self, collection, prefix=None) -> Path:
        if prefix is None:
            prefix = current_app.config.get('DATA_DIR')

        year = self.parser.sensing_date().strftime('%Y')

        base = Path(prefix or '')

        version = entry_version(collection.version)

        scene_id = self.parser.scene_id

        tile_id = self.parser.tile_id()

        path, row = tile_id[:3], tile_id[-3:]

        scene_path = base / collection.name / version / path / row / year / scene_id

        return scene_path

    def compressed_file(self, collection, prefix=None):
        """Retrieve path to the compressed scene .zip."""
        scene_id = self.parser.scene_id
        return self._path(collection, prefix=prefix) / f'{scene_id}.tar.gz'

    def path(self, collection, prefix=None) -> Path:
        """Retrieve the relative path to the Collection on Brazil Data Cube cluster."""
        return self._path(collection, prefix=prefix)


class BaseLandsat(USGSCollection):
    """Define base Landsat Collection."""

    parser_class = LandsatScene

    assets = [
        'MTL.txt', 'ANG.txt', 'radsat_qa.tif',
        'sr_aerosol.tif', 'pixel_qa.tif',
        'sensor_azimuth_band4.tif', 'sensor_zenith_band4.tif',
        'solar_azimuth_band4.tif', 'solar_zenith_band4.tif',
        # Collection 2
        'MTL.xml', 'SR_QA_RADSAT.TIF', 'SR_QA_AEROSOL.TIF', 'MD5.txt', 'GCP.txt', 'VER.jpg', 'VER.txt'
    ]

    def get_files(self, collection, path=None, prefix=None):
        """List all files from Landsat."""
        # TODO: Use parameter path instead
        if path is None:
            path = self.path(collection, prefix)

        path = Path(path)

        output = dict()
        scene_id = self.parser.scene_id

        internal_bands = getattr(self, 'bands', [])

        for f in path.iterdir():
            if f.is_file() and f.suffix.lower() == '.tif':
                band_name = f.stem.replace(f'{scene_id}_', '')

                if (band_name.startswith('sr_') and band_name != 'sr_aerosol') or band_name == 'Fmask4' or \
                        band_name.startswith('nbar_') or band_name.lower().startswith('sr_') or \
                        any(filter(lambda band_ext: band_name in band_ext, internal_bands)):
                    output[band_name] = f

        return output

    def get_assets(self, collection, path=None, prefix=None) -> dict:
        """Retrieve the map of MTL and ANG assets of Landsat product."""
        if path is None:
            path = self.path(collection, prefix=prefix)

        path = Path(path)

        output = dict()

        assets_name = [Path(asset).stem for asset in self.assets]

        collection_level = int(self.parser.level())

        for p in path.glob('*'):
            for asset in self.assets:
                if p.name.endswith(asset):
                    _name = asset.split('.')[0]
                    # Special case for duplicated asset name
                    output[_name if assets_name.count(_name) == 1 or collection_level == 1 else asset] = str(p)
                    break

        return output
