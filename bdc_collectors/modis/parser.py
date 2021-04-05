#
# This file is part of BDC-Collectors.
# Copyright (C) 2020 INPE.
#
# BDC-Collectors is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Defines parsers for MODIS Data."""

from datetime import datetime
from typing import List

from ..base import SceneParser as _SceneParser


class ModisScene(_SceneParser):
    """Define the parser of MODIS Scene identifiers."""

    fragments: List[str]

    def __init__(self, scene_id: str):
        """Create LandsatScene parser."""
        super().__init__(scene_id)

        scene_id = scene_id.replace('.hdf', '').replace('.xml', '')
        fragments = scene_id.split('.')

        if len(fragments) != 5:
            raise RuntimeError(f'Invalid MODIS scene {scene_id}')

        self.fragments = fragments

    def tile_id(self):
        """Retrieve the Vertical Horizontal tile value."""
        return self.fragments[2]

    def sensing_date(self):
        """Retrieve the scene sensing date."""
        return datetime.strptime(self.fragments[1][1:], '%Y%j')

    def processing_date(self):
        """Retrieve the scene processing date."""
        return datetime.strptime(self.fragments[4], '%Y%m%d%H%M%S')

    def satellite(self):
        """Retrieve the satellite name."""
        return ''

    def source(self):
        """Retrieve the scene source name."""
        return self.fragments[0]

    def level(self) -> str:
        """Retrieve the collection level."""
        return ''

    def version(self) -> '':
        """Retrieve the Collection Version."""
        return self.fragments[3]
