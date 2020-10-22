#
# This file is part of BDC-Collectors.
# Copyright (C) 2020 INPE.
#
# BDC-Collectors is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Define simple abstractions for parsing files/data in DGI."""

from datetime import datetime
from typing import List

from ..base import SceneParser


class DGICommonScene(SceneParser):
    """Define simple parser for DGI server."""

    fragments: List[str]

    def __init__(self, scene_id: str):
        """Build a parser."""
        super().__init__(scene_id)

        self.parse()

    def parse(self):
        """Parse a pattern filename for FireRisk."""
        scene_id = self.scene_id

        fragments = scene_id.split('.')

        if len(fragments) == 1:
            fragments = scene_id.split('_')

        self.fragments = fragments

    def sensing_date(self) -> datetime:
        """File sensing date."""
        value = self.fragments[-1]
        if '_' in self.scene_id:
            value = self.fragments[-2]
        return datetime.strptime(value, '%Y%m%d%H')

    def tile_id(self) -> str:
        """Tile id."""
        return ''

    def processing_date(self) -> datetime:
        """File processing date, use same `sensing_date`."""
        return self.sensing_date()

    def satellite(self) -> str:
        """Satellite."""
        return ''

    def source(self):
        """File prefix."""
        return self.fragments[0]
