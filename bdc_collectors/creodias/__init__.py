#
# This file is part of BDC-Collectors.
# Copyright (C) 2020 INPE.
#
# BDC-Collectors is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Defines the structures for CREODIAS API."""

import concurrent
import os
from typing import List

from shapely.geometry import box

from ..base import BaseProvider, SceneResult
from ..exceptions import DataOfflineError
from ..scihub.sentinel2 import Sentinel1, Sentinel2
from .api import Api


def init_provider():
    """Register the CREODIAS provider."""
    # TODO: Register in bdc_catalog.models.Provider

    return dict(
        CREODIAS=CREODIAS
    )


class CREODIAS(BaseProvider):
    """CREODIAS Catalog provider.

    This providers consumes the `CREODIAS API <https://creodias.eu/eo-data-finder-api-manual>`_.

    Notes:
        This provider requires `username` and `password`, respectively.
        You can create an account `CREODIAS Registration <https://portal.creodias.eu/register.php>`_.

        The CREODIAS has implemented Rate Limit in their API services. The limit is 60 requests per minute, per source IP address.
        Make sure to do not overflow 60 requests.
    """

    def __init__(self, **kwargs):
        """Create an instance of ONDA provider."""
        if 'username' not in kwargs or 'password' not in kwargs:
            raise RuntimeError('Missing "username"/"password" for CREODIAS provider.')

        self.api = Api(kwargs['username'], kwargs['password'], progress=kwargs.get('progress', True))
        self.collections['Sentinel-1'] = Sentinel1
        self.collections['Sentinel-2'] = Sentinel2
        self.kwargs = kwargs

    def search(self, query, **kwargs):
        """Search for data set in CREODIAS Provider.

        Based in CREODIAS EO-Data-Finder API, the following products are available in catalog:

            - Sentinel1
            - Sentinel2
            - Sentinel3
            - Sentinel5P
            - Landsat8
            - Landsat7
            - Landsat5
            - Envisat

        You can also specify the processing level `processingLevel` to filter which data set should retrieve.
        For Sentinel2, use `LEVEL1C` for L1 data, `LEVEL2A` as L2, etc.

        Examples:
            >>> from bdc_collectors.creodias import CREODIAS
            >>> provider = CREODIAS(username='theuser@email.com', password='thepass')
            >>> result = provider.search('Sentinel2', bbox=[-54,-12,-52,-10], start_date='2020-01-01', end_date='2020-01-31')

        Args:
            query - The collection name
            **kwargs
        """
        bbox = kwargs.pop('bbox', None)

        if bbox:
            geom = box(*bbox)
            kwargs['geom'] = geom.wkt

        scenes = self.api.search(query, **kwargs)

        return scenes

    def download(self, scene_id: str, output: str, **kwargs):
        """Download scene from CREODIAS API.

        Raises:
            DataOfflineError when scene is not available/offline.

        Examples:
            >>> from bdc_collectors.creodias import CREODIAS
            >>> provider = CREODIAS(username='theuser@email.com', password='thepass')
            >>> output_file = provider.download('S2A_MSIL1C_20201006T132241_N0209_R038_T23KLT_20201006T151824', output='/tmp')
            >>> output_file
            ... '/tmp/S2A_MSIL1C_20201006T132241_N0209_R038_T23KLT_20201006T151824.zip'
        """
        collection = self._guess_collection(scene_id)

        scenes = self.api.search(collection, productIdentifier=f'%{scene_id}%')

        if len(scenes) == 0:
            raise RuntimeError(f'Scene {scene_id} not found.')

        scene = scenes[0]

        if scene['properties']['status'] != 0:
            raise DataOfflineError(scene_id)

        return self._submit_download(scene, output=output, force=kwargs.get('force', False))['path']

    @staticmethod
    def _guess_collection(scene_id) -> str:
        """Try to identify a CREODIAS collection by sceneid."""
        if scene_id.startswith('S2'):
            collection = 'Sentinel2'
        elif scene_id.startswith('S1'):
            collection = 'Sentinel1'
        elif scene_id.startswith('LC08'):
            collection = 'Landsat8'
        elif scene_id.startswith('LE07'):
            collection = 'Landsat7'
        elif scene_id.startswith('LT05'):
            collection = 'Landsat5'
        else:
            raise RuntimeError(f'Cant identify sceneid {scene_id}')

        return collection

    def download_all(self, scenes: List[SceneResult], output: str, **kwargs):
        """Bulk download from CREODIAS provider in parallel.

        Examples:
            >>> from bdc_collectors.creodias import CREODIAS
            >>> provider = CREODIAS(username='theuser@email.com', password='thepass')
            >>> scenes = provider.search('Sentinel2', bbox=[-54,-12,-52,-10], start_date='2020-01-01', end_date='2020-01-31')
            >>> provider.download_all(scenes, output='/tmp')

        Args:
            scenes - List of SceneResult to download
            output - Directory to save
            **kwargs - Optional parameters. You can also set ``max_workers``, which is 2 by default.

        Returns:
            Tuple[List[SceneResult], List[str], List[Exception]]

            Returns the list of Success downloaded, scheduled files and download errors, respectively.
        """
        max_workers = kwargs.pop('max_workers', 2)

        collection = kwargs.get('collection')

        success = []
        scheduled = []
        failed = []

        products = []

        for scene in scenes:
            try:
                result = self.api.search(collection or self._guess_collection(scene.scene_id), productIdentifier=f'%{scene.scene_id}%')

                if len(result) == 0:
                    raise RuntimeError('Not found in provider.')

                products.append(result[0])
            except Exception as e:
                failed.append(scene)

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            tasks = []

            for scene in products:
                tasks.append(
                    executor.submit(self._submit_download, scene, output)
                )

            for task in concurrent.futures.as_completed(tasks):
                if not task.exception() and task.result():
                    success.append(task.result())
                elif task.exception():
                    exception = task.exception()
                    if isinstance(exception, DataOfflineError):
                        scheduled.append(exception.scene_id)
                    else:
                        failed.append(exception)
        return success, scheduled, failed

    def _submit_download(self, scene: SceneResult, output: str, max_retry: int = 10, force: bool = False):
        """Download function used by ThreadExecutor."""
        output = os.path.join(output, f'{scene.scene_id}.zip')

        scene['path'] = self.api.download(scene, output, max_retry=max_retry, force=force)

        return scene
