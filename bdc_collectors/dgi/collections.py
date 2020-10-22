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

from bdc_catalog.models import Collection
from flask import current_app

from ..base import BaseCollection
from .parser import DGICommonScene


class DGICollection(BaseCollection):
    """Define a basic folder (collection) in DGI server."""

    remote_path: str
    format: str

    parser_class = DGICommonScene

    def get_files(self, collection: Collection, path=None, prefix=None) -> Dict[str, Path]:
        """List all files in the collection."""
        if path is None:
            path = self.path(collection, prefix=prefix)

        path = Path(path)

        output = dict()

        if path.exists() and path.is_file():
            output['RISK'] = path

        return output

    def get_assets(self, collection: Collection, path=None, prefix=None) -> Dict[str, str]:
        """Get a list of extra assets contained in collection path."""
        return dict()

    def path(self, collection: Collection, prefix=None) -> Path:
        """Retrieve the relative path to the Collection on Brazil Data Cube cluster."""
        if prefix is None:
            prefix = current_app.config.get('DATA_DIR')

        sensing_date = self.parser.sensing_date()

        year_month = sensing_date.strftime('%Y-%m')

        scene_path = Path(prefix or '') / 'Repository/Archive' / collection.name / year_month

        return scene_path / f'{self.parser.scene_id}.tif'

    def compressed_file(self, collection: Collection, prefix=None) -> Path:
        """Retrieve the path to the compressed file L1."""
        return None


class FireRisk(DGICollection):
    """Structure for wild fire risk."""

    remote_path: str = 'terrama2q/risco_fogo'
    format: str = '.tif'


class Precipitation(DGICollection):
    """Structure for data precipitation, following `IMERG <https://gpm.nasa.gov/data/imerg>`_."""

    remote_path: str = 'terrama2q/prec'
    format: str = '.tif'


class Temperature(DGICollection):
    """Structure for data temperature follwing `Global Forecast System <https://www.ncdc.noaa.gov/data-access/model-data/model-datasets/global-forcast-system-gfs>`_."""

    remote_path: str = 'terrama2q/temp'
    format: str = '.tif'


class RelativeHumidity(DGICollection):
    """Structure for data relative humidity."""

    remote_path: str = 'terrama2q/umid'
    format: str = '.tif'
