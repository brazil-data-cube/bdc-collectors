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

"""Define simple abstractions for products in DGI server."""

from pathlib import Path
from typing import Dict

from flask import current_app

from ..base import BaseCollection
from ..utils import entry_version
from .parser import DGICommonScene


class DGICollection(BaseCollection):
    """Define a basic folder (collection) in DGI server."""

    pattern: str

    parser_class = DGICommonScene

    def get_files(self, collection, path=None, prefix=None) -> Dict[str, Path]:
        """List all files in the collection."""
        if path is None:
            path = self.path(collection, prefix=prefix)

        path = Path(path)

        output = dict()

        if path.exists():
            name = 'default'

            if 'risco' in self.pattern:
                name = 'Fire_Risk'
            elif 'prec' in self.pattern:
                name = 'PREC_IMERG'
            elif 'umid' in self.pattern:
                name = 'RH2M'
            elif 'temperature' in self.pattern:
                name = 'TEMP2M'

            glob = list(path.glob(f'{self.parser.scene_id}*'))

            if len(glob) != 0:
                output[name] = glob[0]

        return output

    def get_assets(self, collection, path=None, prefix=None) -> Dict[str, str]:
        """Get a list of extra assets contained in collection path."""
        return dict()

    def path(self, collection, prefix=None) -> Path:
        """Retrieve the relative path to the Collection on Brazil Data Cube cluster."""
        if prefix is None:
            prefix = current_app.config.get('DATA_DIR')

        sensing_date = self.parser.sensing_date()

        year_month = sensing_date.strftime('%Y-%m')

        version = entry_version(collection.version)

        scene_path = Path(prefix or '') / collection.name / version / year_month

        return scene_path

    def compressed_file(self, collection, prefix=None) -> Path:
        """Retrieve the path to the compressed file L1."""
        return None
