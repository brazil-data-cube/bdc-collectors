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

"""Define the data set of Google for Landsat products."""

import logging
import shutil
import tarfile
from pathlib import Path

try:
    import rasterio
except ImportError:
    rasterio = None

from ..usgs.base import BaseLandsat
from ..utils import working_directory


class GoogleLandsat(BaseLandsat):
    """Define the Landsat product definition."""

    bucket = 'gcp-public-data-landsat'

    def __init__(self, scene_id: str):
        """Create the GoogleLandsat instance."""
        self.parser = self.parser_class(scene_id)

    @property
    def folder(self):
        """Retrieve base folder of Landsat."""
        return self.parser.scene_id

    def get_url(self) -> str:
        """Get the relative URL path in the Landsat bucket."""
        source = self.parser.source()
        tile = self.parser.tile_id()
        scene_id = self.parser.scene_id

        return f'{source}/01/{tile[:3]}/{tile[3:]}/{scene_id}'

    def apply_processing(self, file_path: Path):
        """Apply a function in post download processing.

        This function basically removes the file compression of Tile files
        to be similar USGS scene.
        """
        if file_path.suffix.lower() == '.tif':
            if rasterio is None:
                logging.warning('Missing "rasterio" dependency to remove compression of entry file. Skipping.')
                return

            with rasterio.open(str(file_path), 'r') as source_data_set:
                profile = source_data_set.profile
                raster = source_data_set.read(1)

            profile.pop('compress', '')
            profile.update(dict(
                tiled=False
            ))

            with rasterio.open(str(file_path), 'w', **profile) as target_data_set:
                target_data_set.write_band(1, raster)

    def process(self, downloaded_files: list, output: str) -> str:
        """Compress the downloaded files into scene.tar.gz."""
        compressed_file_path = Path(output) / f'{self.parser.scene_id}.tar.gz'

        with tarfile.open(compressed_file_path, 'w:gz') as compressed_file:
            relative = str(Path(output) / self.parser.scene_id)
            with working_directory(relative):
                for f in downloaded_files:
                    compressed_file.add(str(Path(f).relative_to(relative)))

        shutil.rmtree(str(Path(output) / self.parser.scene_id))

        return str(compressed_file_path)
