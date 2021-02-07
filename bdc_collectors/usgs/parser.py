#
# This file is part of BDC-Collectors.
# Copyright (C) 2020 INPE.
#
# BDC-Collectors is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Defines parsers for USGS catalog."""

from datetime import datetime
from typing import List

from ..base import SceneParser as _SceneParser


class LandsatScene(_SceneParser):
    """Define the parser of Landsat Scene identifiers."""

    fragments: List[str]

    def __init__(self, scene_id: str):
        """Create LandsatScene parser."""
        super().__init__(scene_id)

        fragments = scene_id.split('_')

        if len(fragments) != 7 or fragments[0] not in ('LC08', 'LO08', 'LE07', 'LT05', 'LT04'):
            raise RuntimeError(f'Invalid Landsat scene {scene_id}')

        self.fragments = fragments

    def tile_id(self):
        """Retrieve the WRS2 path row."""
        return self.fragments[2]

    def sensing_date(self):
        """Retrieve the scene sensing date."""
        return datetime.strptime(self.fragments[3], '%Y%m%d')

    def processing_date(self):
        """Retrieve the scene processing date."""
        return datetime.strptime(self.fragments[4], '%Y%m%d')

    def satellite(self):
        """Retrieve the Landsat satellite value (05,07,08...)."""
        part = self.fragments[0]

        return part[-2:]

    def source(self):
        """Retrieve first parameter of scene_id (LC08, etc.)."""
        return self.fragments[0]

    def level(self) -> str:
        """Retrieve the collection level."""
        return self.fragments[-2]
