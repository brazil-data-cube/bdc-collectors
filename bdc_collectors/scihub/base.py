#
# This file is part of BDC-Collectors.
# Copyright (C) 2020 INPE.
#
# BDC-Collectors is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Defines the base structure of SciHub api."""

from pathlib import Path

from bdc_catalog.models import Collection
from flask import current_app

from ..base import BaseCollection
from .parser import Sentinel2Scene


class SentinelCollection(BaseCollection):
    """Define the base collection schema for Sentinel products."""

    parser_class = Sentinel2Scene

    def get_files(self, collection: Collection, path=None, prefix=None):
        """List all files in the collection."""
        if path is None:
            path = self.path(collection, prefix)

        path = Path(path)

        # For Sen2cor files, use recursive and seek for jp2 files
        if collection._metadata and collection._metadata.get('processors'):
            processors = collection._metadata['processors']

            processors = [proc['name'].lower() for proc in processors]

            if 'sen2cor' in processors:
                # Get all .jp2 files
                jp2_files = path.rglob('IMG_DATA/**/*.jp2')
                # Get all .tif (Fmask4 only)
                tif_files = path.rglob('IMG_DATA/*.tif')
                # TODO: Return as iterator instead
                return list(jp2_files) + list(tif_files)
        # Look for default files in root dir
        return super().get_files(collection, path, prefix=prefix)

    def compressed_file(self, collection, prefix=None):
        """Retrieve path to the compressed scene (.zip) on local storage."""
        if prefix is None:
            prefix = current_app.config.get('DATA_DIR')

        year_month = self.parser.sensing_date().strftime('%Y-%m')

        source = self.parser.source()

        sensor = self.parser.fragments[1][:3]

        folder = '{}_{}'.format(source[:2], sensor)

        scene_path = Path(prefix or '') / 'Repository/Archive' / folder / year_month

        return scene_path / '{}.zip'.format(self.parser.scene_id)

    def path(self, collection: Collection, prefix=None) -> Path:
        """Retrieve the relative path to the Collection on Brazil Data Cube cluster."""
        if prefix is None:
            prefix = current_app.config.get('DATA_DIR')

        sensing_date = self.parser.sensing_date()

        year_month = sensing_date.strftime('%Y-%m')

        scene_path = Path(prefix or '') / 'Repository/Archive' / collection.name / year_month

        scene_path = scene_path / self.parser.scene_id

        return scene_path

    def get_assets(self, collection, path=None, prefix=None) -> dict:
        """Retrieve the map assets of Sentinel product."""
        if path is None:
            path = self.path(collection, prefix=prefix)

        path = Path(path)

        mtd = path / 'MTD_MSIL2A.xml'

        if mtd.exists():
            # TODO: Check for other files (AOT as band??)
            output = dict(
                MTD=str(mtd),
            )

        return output
