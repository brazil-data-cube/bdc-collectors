#
# This file is part of BDC-Collectors.
# Copyright (C) 2020 INPE.
#
# BDC-Collectors is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Defines the structures for CREODIAS API.

The CREODIAS API is an alternative to download Earth Observation datasets related with Copernicus
program. It serves the Sentinel-2 and others datasets in their platform.

Basic usage::

    from flask import current_app

    ext = current_app.extensions['bdc_collector']
    provider_klass = ext.get_provider("CREODIAS")

    provider = provider_klass("user", "passwd")
    provider.search(...)
"""

import concurrent.futures
import os
from typing import List

from shapely.geometry import box

from ..base import BaseProvider, SceneResult
from ..exceptions import DataOfflineError
from ..scihub.sentinel2 import Sentinel1, Sentinel2
from .api import Api


def init_provider():
    """Register the CREODIAS provider.

    Note:
        Called once by ``CollectorExtension``.
    """
    return dict(
        CREODIAS=CREODIAS
    )


class CREODIAS(BaseProvider):
    """CREODIAS Catalog provider.

    This providers consumes the `CREODIAS API <https://creodias.eu/eo-data-finder-api-manual>`_.

    Note:
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

            - ``Sentinel1``
            - ``Sentinel2``
            - ``Sentinel3``
            - ``Sentinel5P``
            - ``Landsat8``
            - ``Landsat7``
            - ``Landsat5``
            - ``Envisat``

        You can also specify the processing level ``processingLevel`` to filter which data set should retrieve.
        For Sentinel2, use ``LEVEL1C`` for L1 data, ``LEVEL2A`` as L2, etc.

        Args:
            query - The collection name

        Keyword Args:
            start_date (str|datetime): Start date time filter
            end_date (str|datetime): End date time filter
            geom (str): Region of Interest (WKT)
            bbox (Tuple[float,float,float,float]): The bounding box values ordened as
                ``west``, ``south``, ``east``, ``north``.
            status (str): CREODIAS API Status for data sets. Defaults to ``all``.
        """
        bbox = kwargs.pop('bbox', None)

        if bbox:
            geom = box(*bbox)
            kwargs['geom'] = geom.wkt

        scenes = self.api.search(query, **kwargs)

        return scenes

    def download(self, scene_id: str, output: str, **kwargs):
        """Download scene from CREODIAS API.

        Note:
            When download is interrupted, the file is not removed.
            The ``temporary`` file is defined by ``.tmp`` in the end of filename.
            Whenever a download is triggered and there is already a ``temp`` file,
            the module will try to resume download.

        Args:
            scene_id: The Scene Identifier to download
            output: The base output directory

        Keyword Args:
            force (bool): Flag to re-download file (do not use cache). Defaults to ``False``.

        Raises:
            DataOfflineError: when scene is not available/offline.
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

        Args:
            scenes - List of SceneResult to download
            output - Directory to save
        Keyword Args:
            max_workers (int): Number of parallel download. Defaults to ``2``.
            collection (str): The CREODIAS Collection name.

        Returns:
            Tuple[List[SceneResult], List[str], List[Exception]]
                Returns the list of ``success`` downloaded, ``scheduled`` files and download ``errors``, respectively.
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
