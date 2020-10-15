#
# This file is part of BDC-Collectors.
# Copyright (C) 2020 INPE.
#
# BDC-Collectors is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Define the providers to deal with STAC Element84."""
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List

import requests
from shapely.geometry import box, mapping
from stac import STAC

from ..base import BaseProvider, SceneResult
from ..exceptions import DownloadError
from ..scihub.parser import Sentinel2Scene
from ..usgs import LandsatScene
from ..utils import download_stream


def init_provider():
    """Init provider factory loader."""
    return dict(EarthSearch=EarthSearch)


class EarthSearch(BaseProvider):
    """Define a simple abstraction of Provider for Element84.

    It was designed to download Sentinel-2 COGS from
    `Sentinel-2 Cloud-Optimized GeoTIFFs <https://registry.opendata.aws/sentinel-2-l2a-cogs/>`_
    """

    def __init__(self, **kwargs):
        """Build STAC provider for Element84."""
        access_token = kwargs.pop('access_token', None)

        self.kwargs = kwargs
        self.api = STAC('https://earth-search.aws.element84.com/v0', access_token=access_token)
        self.progress = kwargs.get('progress')

    def search(self, query, *args, **kwargs) -> List[SceneResult]:
        """Search for scenes in STAC."""
        options = dict()

        if 'start_date' in kwargs:
            options['time'] = f'{kwargs.get("start_date")}/{kwargs.get("end_date")}'

        if 'bbox' in kwargs:
            options['intersects'] = mapping(box(*kwargs['bbox']))

        options['collection'] = query

        res = self.api.search(filter=options)

        # TODO: Implement next page as iterator or check stac.py support
        return [
            SceneResult(
                scene_id=f['properties']['sentinel:product_id'],
                cloud_cover=f['properties']['sentinel:cloud_cover'],
                **f
            )
            for f in res['features']
        ]

    @staticmethod
    def _guess_parser(scene_id: str):
        """Get the supported parser for Scene."""
        if scene_id.startswith('S2'):
            return Sentinel2Scene(scene_id)
        return LandsatScene(scene_id)

    def download(self, scene_id: str, *args, **kwargs) -> str:
        """Download files from STAC Element 84."""
        output = kwargs['output']

        collection = kwargs['dataset']

        parsed = self._guess_parser(scene_id)

        stac_collection = self.api.collection(collection)

        product = parsed.fragments[1][-3:]

        item_id = f'{parsed.source()}_{parsed.tile_id()}_{parsed.sensing_date().strftime("%Y%m%d")}_0_{product}'

        feature = stac_collection.get_items(item_id=item_id)

        if feature.get('code'):
            raise RuntimeError(f'Scene {scene_id} not found for collection {collection}.')

        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp) / item_id

            for asset_name, asset in feature['assets'].items():
                self._download(asset['href'], str(tmp_path))

            shutil.move(str(tmp_path), output)

        return output

    def _download(self, link, output):
        """Download asset from STAC."""
        file_name = Path(link).name

        path = Path(output) / file_name

        response = requests.get(link, stream=True, timeout=90)

        download_stream(str(path), response, progress=self.progress)
