#
# This file is part of BDC-Collectors.
# Copyright (C) 2020 INPE.
#
# BDC-Collectors is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Define simple abstractions for products in DGI server."""

from pathlib import Path
from typing import Dict

from flask import current_app

from ..base import BaseCollection
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

        version = 'v{0:03d}'.format(collection.version)

        scene_path = Path(prefix or '') / collection.name / version / year_month

        return scene_path

    def compressed_file(self, collection, prefix=None) -> Path:
        """Retrieve the path to the compressed file L1."""
        return None
