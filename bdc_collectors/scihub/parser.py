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

"""Defines the base structure of SciHub api."""

from datetime import datetime
from typing import List

from ..base import SceneParser


class Sentinel2Scene(SceneParser):
    """Define the parser of Sentinel Scene identifiers."""

    fragments: List[str]

    def __init__(self, scene_id: str):
        """Create the parser Sentinel2Scene."""
        super().__init__(scene_id)

        fragments = scene_id.split('_')

        if len(fragments) != 7 or not fragments[0].startswith("S2"):
            raise RuntimeError(f'Invalid sentinel scene {scene_id}')

        self.fragments = fragments

    def tile_id(self):
        """Retrieve the tile id value."""
        return self.fragments[5][1:]

    def sensing_date(self):
        """Retrieve the scene sensing date."""
        return datetime.strptime(self.fragments[2], '%Y%m%dT%H%M%S')

    def processing_date(self):
        """Retrieve the scene processing date."""
        return datetime.strptime(self.fragments[-1], '%Y%m%dT%H%M%S')

    def satellite(self):
        """Retrieve the Sentinel satellite - 2A/2B."""
        part = self.fragments[0]

        return part[-2:]

    def source(self):
        """Retrieve the scene first parameter (S2A/S2B)."""
        return self.fragments[0]


class Sentinel1Scene(SceneParser):
    """Define the parser of Sentinel 1 Scene identifiers."""

    fragments: List[str]

    def __init__(self, scene_id: str):
        """Create the parser SentinelScene."""
        super().__init__(scene_id)

        fragments = scene_id.split('_')

        if len(fragments) != 9 or not fragments[0].startswith("S1"):
            raise RuntimeError(f'Invalid sentinel scene {scene_id}')

        self.fragments = fragments

    def tile_id(self):
        """Retrieve the tile id value."""
        return self.fragments[6]

    def sensing_date(self):
        """Retrieve the scene sensing date."""
        return datetime.strptime(self.fragments[4], '%Y%m%dT%H%M%S')

    def processing_date(self):
        """Retrieve the scene processing date."""
        return datetime.strptime(self.fragments[5], '%Y%m%dT%H%M%S')

    def satellite(self):
        """Retrieve the Sentinel satellite - 2A/2B."""
        part = self.fragments[0]

        return part[-2:]

    def source(self):
        """Retrieve the scene first parameter (S2A/S2B)."""
        return self.fragments[0]


class Sentinel3Scene(SceneParser):
    """Define the parser of Sentinel 3 Scene identifiers.
    
    Follows the `Sentinel-3 Naming Convention <https://sentinels.copernicus.eu/web/sentinel/user-guides/sentinel-3-olci/naming-convention>`_.
    """

    fragments: List[str]

    def __init__(self, scene_id: str):
        """Create the parser SentinelScene."""
        super().__init__(scene_id)

        fragments = scene_id.split('_')

        if len(fragments) != 18 or not fragments[0].startswith('S3'):
            raise RuntimeError(f'Invalid sentinel scene {scene_id}')

        self.fragments = fragments

    def tile_id(self):
        """Retrieve the tile id value."""
        return None

    def sensing_date(self):
        """Retrieve the scene sensing date."""
        return datetime.strptime(self.fragments[7], '%Y%m%dT%H%M%S')

    def processing_date(self):
        """Retrieve the scene processing date."""
        return datetime.strptime(self.fragments[9], '%Y%m%dT%H%M%S')

    def satellite(self):
        """Retrieve the Sentinel satellite - 3A/3B."""
        part = self.fragments[0]

        return part[-2:]

    def source(self):
        """Retrieve the scene first parameter (S3A/S3B)."""
        return self.fragments[0]

    def datatype_id(self):
        """Return the scene data type identifier."""
        return self.fragments[3:7]

    def level(self) -> str:
        """Return the scene level."""
        return self.fragments[2]

    def datasource(self) -> str:
        """Retrieve the data source/consume name."""
        return self.fragments[1]
