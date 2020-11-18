#
# This file is part of BDC-Collectors.
# Copyright (C) 2020 INPE.
#
# BDC-Collectors is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Base definitions for USGS catalog."""

from pathlib import Path

from bdc_catalog.models import Collection
from flask import current_app

from ..base import BaseCollection
from .parser import LandsatScene


class BaseLandsat(BaseCollection):
    """Define base Landsat Collection."""

    parser_class = LandsatScene

    assets = [
        'MTL.txt', 'ANG.txt', 'radsat_qa.tif',
        'sr_aerosol.tif', 'pixel_qa.tif',
        'sensor_azimuth_band4.tif', 'sensor_zenith_band4.tif',
        'solar_azimuth_band4.tif', 'solar_zenith_band4.tif'
    ]

    def get_files(self, collection, path=None, prefix=None):
        """List all files from Landsat."""
        # TODO: Use parameter path instead
        if path is None:
            path = self.path(collection, prefix)

        path = Path(path)

        output = dict()
        scene_id = self.parser.scene_id

        for f in path.iterdir():
            if f.is_file() and f.suffix.lower() == '.tif':
                band_name = f.stem.replace(f'{scene_id}_', '')

                if (band_name.startswith('sr_') and band_name != 'sr_aerosol') or band_name == 'Fmask4' or \
                        band_name.startswith('nbar_'):
                    output[band_name] = f

        return output

    def path(self, collection: Collection, prefix=None) -> Path:
        """Retrieve the relative path to the Collection on Brazil Data Cube cluster.

        Example:
            >>> collection = Collection.query().filter(Collection.name == 'LC8_DN').first_or_404()
            >>> landsat_parser = LandsatScene('LC08_L1TP_223064_20200831_20200906_01_T1')
            >>> scene = BaseCollection(collection=collection, landsat_parser)
            >>> print(str(scene.path(prefix='/gfs')))
            ... '/gfs/Repository/Archive/LC8_DN/2015-07/223064/'
        """
        if prefix is None:
            prefix = current_app.config.get('DATA_DIR')

        sensing_date = self.parser.sensing_date()

        year_month = sensing_date.strftime('%Y-%m')

        scene_path = Path(prefix or '') / 'Repository/Archive' / collection.name / year_month / self.parser.tile_id()

        return scene_path

    def compressed_file(self, collection, prefix=None):
        """Retrieve path to the compressed scene .zip."""
        if prefix is None:
            prefix = current_app.config.get('DATA_DIR')

        year_month = self.parser.sensing_date().strftime('%Y-%m')

        product_version = int(self.parser.satellite())

        folder = '{}{}'.format(self.parser.source()[:2], product_version)

        scene_path = Path(prefix or '') / 'Repository/Archive' / folder / year_month / self.parser.tile_id()

        return scene_path / '{}.tar.gz'.format(self.parser.scene_id)

    def get_assets(self, collection, path=None, prefix=None) -> dict:
        """Retrieve the map of MTL and ANG assets of Landsat product."""
        if path is None:
            path = self.path(collection, prefix=prefix)

        path = Path(path)

        output = dict()

        for p in path.glob('*'):
            for asset in self.assets:
                if p.name.endswith(asset):
                    output[asset.split('.')[0]] = str(p)
                    break

        return output
