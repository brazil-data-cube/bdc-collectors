#
# This file is part of BDC-Collectors.
# Copyright (C) 2020 INPE.
#
# BDC-Collectors is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Define the structures for USGS Earth Explorer Provider access."""

import logging
from typing import List

from landsatxplore.api import API, is_product_id
from landsatxplore.earthexplorer import EE_DOWNLOAD_URL, EarthExplorer
from landsatxplore.exceptions import EarthExplorerError

from ..base import BaseProvider, SceneResult
from ..exceptions import DownloadError
from .landsat5 import Landsat5
from .landsat7 import Landsat7
from .landsat8 import Landsat8
from .parser import LandsatScene


def init_provider():
    """Register the USGS provider."""
    # TODO: Register in bdc_catalog.models.Provider

    return dict(
        USGS=USGS
    )


class USGS(BaseProvider):
    """Define the USGS provider.

    This providers consumes the `USGS EarthExplorer <https://earthexplorer.usgs.gov/>`_ catalog.
    """

    api: API

    def __init__(self, **kwargs):
        """Create instance of USGS provider."""
        self.collections['LANDSAT_TM_C1'] = Landsat5
        self.collections['LANDSAT_ETM_C1'] = Landsat7
        self.collections['LANDSAT_8_C1'] = Landsat8

        lazy = kwargs.get('lazy')

        if 'username' not in kwargs or 'password' not in kwargs:
            raise RuntimeError('Missing "username"/"password" for USGS provider.')

        self.kwargs = kwargs

        if lazy:
            self.api = None
        else:
            self.api = API(self.kwargs['username'], self.kwargs['password'])

    def _api(self):
        """Lazy API instance."""
        if self.api is None:
            self.api = API(self.kwargs['username'], self.kwargs['password'])

    def __del__(self):
        """Logout in USGS on exit."""
        if self.api:
            self.api.logout()

    def search(self, query, *args, **kwargs) -> List[SceneResult]:
        """Search for data set in USGS catalog."""
        self._api()

        options = dict(
            max_cloud_cover=kwargs.get('cloud_cover', 100),
            start_date=kwargs.get('start_date'),
            end_date=kwargs.get('end_date'),
            max_results=kwargs.get('max_results', 50000)
        )

        if 'bbox' in kwargs:
            bbox = kwargs['bbox']
            # w,s,e,n  => s,w,n,e due bug https://github.com/yannforget/landsatxplore/blob/master/landsatxplore/datamodels.py#L49
            options['bbox'] = [bbox[1], bbox[0], bbox[3], bbox[2]]

        results = self.api.search(query, **options)

        valid_scene = self._valid_scene

        if 'validate' in kwargs:
            valid_scene = kwargs['validate']

            if not callable(valid_scene):
                raise ValueError(f'Invalid validate. Expected a callable(scene:dict), but got {valid_scene}')

        return [
            SceneResult(scene['displayId'], scene['cloudCover'], link=scene['downloadUrl'], **scene)
            for scene in results if valid_scene(scene)
        ]

    def _valid_scene(self, scene: dict) -> bool:
        """Filter validator for invalid scenes.

        Sometimes, the USGS Catalog returns wrong scene_ids and this functions removes that holes.
        """
        if scene['displayId'].endswith('RT') or scene['displayId'].startswith('LO08'):
            return False

        xmin, ymin, xmax, ymax = [float(value) for value in scene['sceneBounds'].split(',')]

        # TODO: Check data integrity
        # Sometimes the USGS responds invalid bounding box scenes while searching in EarthExplorer Catalog.
        # w=-60.87065, n=-10.18204, e=-57.66829, s=-12.18696
        # The expected scenes are:
        # 228067, 228068, 228069, 229067, 229068, 229069, 230067, 230068, 230069.
        # However, an invalid scene will be found (074068, 074067).
        if xmin - xmax < -3:
            logging.warning(f'Scene {scene["displayId"]} inconsistent.')
            return False

        return True

    def download(self, scene_id: str, *args, **kwargs):
        """Download Landsat product from USGS."""
        self._api()

        destination = kwargs.get('output')

        explorer = EarthExplorer(self.kwargs['username'], self.kwargs['password'])

        try:
            file_name = explorer.download(scene_id, destination)
        except EarthExplorerError as e:
            raise DownloadError(str(e))

        return file_name
