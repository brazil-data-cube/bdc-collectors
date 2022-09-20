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
