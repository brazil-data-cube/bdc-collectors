#
# This file is part of BDC-Collectors.
# Copyright (C) 2020 INPE.
#
# BDC-Collectors is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Define the implementation of Sentinel Provider."""

from datetime import datetime
from typing import List

import dateutil.parser
from sentinelsat import SentinelAPI, SentinelAPILTAError
from shapely.geometry import box

from ..base import BaseProvider, SceneResult
from ..exceptions import DataOfflineError, DownloadError
from .clients import UserClients
from .sentinel2 import Sentinel1, Sentinel2


def init_provider():
    """Register sentinel provider."""
    # TODO: Register in bdc_catalog.models.Provider
    return dict(
        SciHub=SciHub
    )


def _get_date_time(date) -> datetime:
    """Get a datetime object from entry."""
    if isinstance(date, datetime):
        return date

    return dateutil.parser.isoparse(date)


class SciHub(BaseProvider):
    """Define a simple implementation of Sentinel api.

    This module uses `sentinel-sat` to search and to download files from Copernicus.

    TODO: Document how to download multiple files using multiple accounts.
    """

    def __init__(self, *users, **kwargs):
        """Create sentinel api instance."""
        users_context = list(users)

        show_progress = kwargs.get('progress', False)
        parallel = kwargs.get('parallel', False)

        self.progress = show_progress

        if not users:
            if 'username' not in kwargs or 'password' not in kwargs:
                raise RuntimeError('Missing "username"/"password" for USGS provider.')

            auth = kwargs

            self.parallel = parallel

            if parallel:
                users_context.append(auth)

            self.kwargs = kwargs
        else:
            self.parallel = True
            auth = users[0]

        self.api = SentinelAPI(auth['username'], auth['password'], show_progressbars=show_progress)

        if self.parallel:
            self.clients = UserClients(users_context)

        self.collections['Sentinel-1'] = Sentinel1
        self.collections['GRD'] = Sentinel1
        self.collections['Sentinel-2'] = Sentinel2
        self.collections['S2MSI1C'] = Sentinel2
        self.collections['S2MSI2A'] = Sentinel2

    def search(self, query, **kwargs):
        """Search for products on Sentinel provider.

        Args:
            query - Product name
            **kwargs - Optional parameters (start_date/end_date/cloud_cover, etc)
        """
        bbox = kwargs.pop('bbox', None)

        product_type = query

        # TODO: Support download others sentinel
        platform = kwargs.pop('platform', None) or 'Sentinel-2'

        cloud_cover = kwargs.pop('cloud_cover', None)

        options = kwargs.copy()
        options['platformname'] = platform
        options['producttype'] = product_type

        if bbox:
            envelope = box(*bbox)
            options['area'] = envelope.wkt

        if 'start_date' in kwargs and 'end_date':
            start_date = _get_date_time(options.pop('start_date'))
            end_date = _get_date_time(options.pop('end_date'))

            options['date'] = start_date, end_date

        if platform == 'Sentinel-2' and cloud_cover:
            options['cloudcoverpercentage'] = (0, cloud_cover)

        scenes = self.api.query(**options)

        return [
            SceneResult(scenes[scene]['title'], scenes[scene].get('cloudcoverpercentage'), **scenes[scene])
            for scene in scenes
        ]

    def download(self, scene_id: str, output: str, **kwargs) -> str:
        """Try to download data from Copernicus.

        Raises:
            DownloadError when scene not found.
            DataOfflineError when scene is not available/offline.
        """
        meta = self.api.query(filename=f'{scene_id}*')

        if len(meta) < 0:
            raise DownloadError(f'Scene id {scene_id} not found.')

        api = self.api

        # When parallel support set, get an available client from Redis
        if self.parallel:
            client = self.clients.get_user()

            api = SentinelAPI(client.username, client.password, show_progressbars=self.progress)

        uuid = list(meta)[0]

        entry = api.download(uuid, output)

        if not entry['Online']:
            raise DataOfflineError(scene_id)

        return entry['path']

    def download_all(self, scenes: List[SceneResult], output: str, **kwargs):
        """Download multiple scenes from Sentinel-Sat API.

        Args:
            scenes - List of scenes found by search method.
            output - Output directory
            **kwargs - Others parameters to be attached into sentinel-sat.
        """
        uuid_scenes_map = {item['uuid']: item.scene_id for item in scenes}

        try:
            res = self.api.download_all(uuid_scenes_map, directory_path=output, **kwargs)

            return res
        except SentinelAPILTAError as e:
            raise DownloadError(f'Error in Sentinel LongTermArchive - {str(e)}')
