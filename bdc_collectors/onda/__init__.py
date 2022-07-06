#
# This file is part of BDC-Collectors.
# Copyright (C) 2020 INPE.
#
# BDC-Collectors is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Defines the structures for ONDA Catalogue."""

import concurrent
from datetime import datetime
from typing import List

from ..base import BaseProvider, SceneResult
from ..exceptions import DataOfflineError
from .api import Api


def init_provider():
    """Register the ONDA provider."""
    return dict(
        ONDA=ONDA
    )


class ONDA(BaseProvider):
    """ONDA Catalog provider.

    This providers consumes the `ONDA Open Catalogue <https://www.onda-dias.eu/cms/knowledge-base/catal-open-the-catalogue/>`_.

    Note:
        This provider requires `username` and `password`, respectively.
        You can create an account `ONDA Registration <https://onda-dias.eu/userportal/self-registration>`_
    """

    def __init__(self, **kwargs):
        """Create an instance of ONDA provider."""
        if 'username' not in kwargs or 'password' not in kwargs:
            raise RuntimeError('Missing "username"/"password" for ONDA provider.')

        self.api = Api(kwargs['username'], kwargs['password'], progress=kwargs.get('progress', True))
        self.kwargs = kwargs

    def search(self, query, **kwargs):
        """Search for data set in ONDA Provider.

        Currently, it is not supported yet.
        """
        # TODO: Implement search using https://www.onda-dias.eu/cms/knowledge-base/odata-querying-all-the-entities-of-the-onda-odata-api/
        raise RuntimeError('The method search is not supported yet.')

    def download(self, scene_id: str, output: str, **kwargs):
        """Download scene from ONDA catalogue API.

        Raises:
            DataOfflineError when scene is not available/offline.
        """
        meta = self.api.search_by_scene_id(scene_id)

        if meta['offline']:
            self.api.order(meta['id'])

            raise DataOfflineError(scene_id)

        file_name = self.api.download(scene_id, output)

        return file_name

    def download_all(self, scenes: List[SceneResult], output: str, **kwargs):
        """Bulk download from ONDA provider.

        Args:
            scenes - List of SceneResult to download (Use SciHub to search and pass result here)
            output - Directory to save
            **kwargs - Optional parameters. You can also set ``max_workers``, which is 2 by default.
        """
        max_workers = kwargs.pop('max_workers', 2)

        success = []
        scheduled = []
        failed = []

        for scene in scenes:
            try:
                meta = self.api.search_by_scene_id(scene.scene_id)

                scene.update(meta)
            except RuntimeError:
                failed.append(scene)

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            tasks = []

            for scene in scenes:
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

        return success, scheduled, failed

    def _submit_download(self, scene: SceneResult, output):
        """Download function used by ThreadExecutor."""
        if scene['offline']:
            self.api.order(scene['id'])

            raise DataOfflineError(scene.scene_id)

        scene['path'] = self.api.download(scene.scene_id, output)

        return scene
