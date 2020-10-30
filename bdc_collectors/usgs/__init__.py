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


FIELD_SEARCH_MAP = dict(
    LANDSAT_8_C1=dict(
        scene='5e83d0b84d321b85',
        path='5e83d0b81d20cee8',
        row='5e83d0b849ed5ee7'
    ),
    LANDSAT_ETM_C1=dict(
        scene='5e83a507ba68271e',
        path='5e83a507b9aa5140',
        row='5e83a5074670b94e'
    ),
    LANDSAT_TM_C1=dict(
        scene='5e83d08fd4594aae',
        path='5e83d08f6487afc7',
        row='5e83d08ffa032790'
    )
)
"""Type which maps the supported field filters on EarthExplorer."""


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

    def _search(self, query, **options):
        if options.get('additionalCriteria'):
            params = dict(
                datasetName=query,
                maxResults=options['max_results'],
                maxCloudCover=100,
                additionalCriteria=options['additionalCriteria']
            )
            response = self.api.request('search', **params)

            return response['results']
        return self.api.search(query, **options)

    @staticmethod
    def _criteria(value: str, filter_type: str = 'value', operand: str = '=', field_id=None, **opts) -> dict:
        options = dict(filterType=filter_type, fieldId=field_id)

        if filter_type == 'between':
            options['firstValue'] = value
            options['secondValue'] = opts['secondValue']
        elif filter_type == 'value':
            options['value'] = value
            options['operand'] = operand

        return options

    def search(self, query, *args, **kwargs) -> List[SceneResult]:
        """Search for data set in USGS catalog."""
        self._api()

        options = dict(
            max_cloud_cover=kwargs.get('cloud_cover', 100),
            start_date=kwargs.get('start_date'),
            end_date=kwargs.get('end_date'),
            max_results=kwargs.get('max_results', 50000)
        )

        if kwargs.get('additionalCriteria'):
            options['additionalCriteria'] = kwargs['additionalCriteria']
        elif 'bbox' in kwargs and kwargs['bbox'] is not None:
            bbox = kwargs['bbox']
            # w,s,e,n  => s,w,n,e due bug https://github.com/yannforget/landsatxplore/blob/master/landsatxplore/datamodels.py#L49
            options['bbox'] = [bbox[1], bbox[0], bbox[3], bbox[2]]
        elif kwargs.get('filename') or kwargs.get('scene_id'):
            scene_id = kwargs.get('filename') or kwargs.get('scene_id')

            field_map = FIELD_SEARCH_MAP[query]

            criteria = self._criteria(scene_id.replace('*', ''), field_id=field_map['scene'])
            options['additionalCriteria'] = criteria
        elif kwargs.get('tile'):
            path, row = kwargs['tile'][:3], kwargs['tile'][-3:]

            field_map = FIELD_SEARCH_MAP[query]

            path_criteria = self._criteria(path, filter_type='between',
                                           field_id=field_map['path'], secondValue=path)

            row_criteria = self._criteria(row, filter_type='between',
                                          field_id=field_map['row'], secondValue=row)

            options['additionalCriteria'] = dict(
                filterType='and',
                childFilters=[path_criteria, row_criteria]
            )

        results = self._search(query, **options)

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
