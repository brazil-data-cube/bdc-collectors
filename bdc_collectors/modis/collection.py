#
# This file is part of BDC-Collectors.
# Copyright (C) 2020 INPE.
#
# BDC-Collectors is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Define the components to deal with MODIS Datasets."""

from pathlib import Path
from typing import Dict

from flask import current_app

from ..base import BaseCollection
from .parser import ModisScene


class ModisCollection(BaseCollection):
    """Represent an Data Collection for NASA MODIS products."""

    parser_class = ModisScene

    def get_assets(self, collection, path=None, prefix=None) -> Dict[str, str]:
        """Get a list of extra assets contained in collection path.

        Args:
            collection - A instance of bdc_catalog.models.Collection context.
            path - Path to seek for the files
            prefix - Extra prefix. By default, used the Brazil Data Cube Cluster.

        Returns:
            Dict[str, str]
            Map of asset_name and the absolute asset in disk.
        """
        return dict()

    def path(self, collection, prefix=None, cube_prefix=None) -> Path:
        """Retrieve the relative path to the Collection on Brazil Data Cube cluster."""
        if prefix is None:
            prefix = current_app.config.get('DATA_DIR')

        year = str(self.parser.sensing_date().year)
        tile = self.parser.tile_id()
        version = 'v{0:03d}'.format(collection.version)
        scene_id = self.parser.scene_id

        relative = Path(collection.name) / version / tile[:3] / tile[3:] / year / scene_id

        scene_path = Path(prefix or '') / relative

        return scene_path

    def compressed_file(self, collection, prefix=None) -> Path:
        """Show the path to the MODIS HDF file."""
        path = self.path(collection=collection, prefix=prefix, cube_prefix='Archive')

        return path / f'{self.parser.scene_id}.hdf'
