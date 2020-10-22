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

        self._parse()

    def _parse(self):
        """Parse a pattern filename for FireRisk."""
        scene_id = self.scene_id

        fragments = scene_id.split('.')

        if len(fragments) != 3:
            raise RuntimeError(f'Invalid scene_id. {scene_id}')

        self.fragments = fragments

    def sensing_date(self) -> datetime:
        """File sensing date."""
        return datetime.strptime(self.fragments[-1], '%Y%m%d%H')

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


class DGITemperatureUmidScene(DGICommonScene):
    """Parse the filename of temperature and relative humidity."""

    def _parse(self):
        """Parse a pattern filename for Data temperature and Relative Humidity."""
        scene_id = self.scene_id

        fragments = scene_id.split('.')

        if len(fragments) != 4:
            raise RuntimeError(f'Invalid scene_id. {scene_id}')

        self.fragments = fragments
