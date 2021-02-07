#
# This file is part of BDC-Collectors.
# Copyright (C) 2020 INPE.
#
# BDC-Collectors is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Define the structures for USGS Earth Explorer Provider access."""

import logging
import re
from typing import List, Type

from shapely.geometry import shape

from ._collections import get_resolver
from .base import USGSCollection
from ..base import BaseProvider, SceneResult, BaseCollection
from ..exceptions import DownloadError
from .api import EarthExplorer, LandsatApi
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


PATH_ENTRIES = [
    re.compile('WRS Path'),
    re.compile('Horizontal Tile')
]
ROW_ENTRIES = [
    re.compile('WRS Row'),
    re.compile('Vertical Tile')
]
SCENE_ENTRIES = [
    re.compile('Landsat Product Identifier'),
    re.compile('Entity ID')
]


class USGS(BaseProvider):
    """Define the USGS provider.

    This providers consumes the `USGS EarthExplorer <https://earthexplorer.usgs.gov/>`_ catalog.

    This module follows the new experimental `API 1.5 <https://m2m.cr.usgs.gov/api/docs/json/>`_.

    Notes:
         Remember to call `.disconnect()` to avoid blocked IP's on USGS Server.
    """

    api: LandsatApi

    def __init__(self, **kwargs):
        """Create instance of USGS provider."""
        self._set_default_collections(['landsat_tm_c1', 'landsat_tm_c2_l1', 'landsat_tm_c2_l2'], Landsat5)
        self._set_default_collections(['landsat_etm_c1', 'landsat_etm_c2_l1', 'landsat_etm_c2_l2'], Landsat7)
        self._set_default_collections(['landsat_8_c1', 'landsat_ot_c2_l1', 'landsat_ot_c2_l2'], Landsat8)

        lazy = kwargs.get('lazy')

        if 'username' not in kwargs or 'password' not in kwargs:
            raise RuntimeError('Missing "username"/"password" for USGS provider.')

        self.kwargs = kwargs

        if lazy:
            self.api = None
        else:
            self.api = LandsatApi(self.kwargs['username'], self.kwargs['password'])
            self.ee = EarthExplorer(self.kwargs['username'], self.kwargs['password'])

    def _set_default_collections(self, datasets, data_type):
        for dataset in datasets:
            self.collections[dataset.lower()] = data_type
            self.collections[dataset.upper()] = data_type

    def _api(self):
        """Lazy API instance."""
        if self.api is None:
            self.api = LandsatApi(self.kwargs['username'], self.kwargs['password'])
            self.ee = EarthExplorer(self.kwargs['username'], self.kwargs['password'])

    def get_collector(self, collection: str) -> Type[BaseCollection]:
        if collection.lower() not in self.collections:
            return USGSCollection
        return super().get_collector(collection.lower())

    @staticmethod
    def _criteria(value: str, filter_type: str = 'value', operand: str = '=', field_id=None, **opts) -> dict:
        options = dict(filterType=filter_type, filterId=field_id)

        if filter_type == 'between':
            options['firstValue'] = value
            options['secondValue'] = opts['secondValue']
        elif filter_type == 'value':
            options['value'] = value
            options['operand'] = operand

        return options

    def _get_filter(self, dataset, field: str = 'fieldLabel', context: str = None):
        filters = self.api.filters(dataset)

        for entry in filters:
            if field not in entry:
                raise RuntimeError(f'Filter Error. {field}, {context}')

            if context == 'path' and any(regex.match(entry[field]) for regex in PATH_ENTRIES):
                return entry[field]

            if context == 'row' and any(regex.match(entry[field]) for regex in ROW_ENTRIES):
                return entry[field]

            if context == 'scene' and any(regex.match(entry[field]) for regex in SCENE_ENTRIES):
                return entry[field]

        return None

    def search(self, query, *args, **kwargs) -> List[SceneResult]:
        """Search for data set in USGS catalog."""
        self._api()

        options = dict(
            datasetName=query,
            maxResults=kwargs.get('max_results', 50000),
            sceneFilter=dict(
                spatialFilter=None
            )
        )

        # Look for all filters
        self.api.filters(query)

        if kwargs.get('sceneFilter'):
            options['sceneFilter'] = kwargs['sceneFilter']
        else:
            options.setdefault('sceneFilter', dict())

            if kwargs.get('start_date'):
                options['sceneFilter']['acquisitionFilter'] = dict(
                    start=kwargs['start_date'],
                    end=kwargs['end_date']
                )

            if kwargs.get('cloudCoverFilter'):
                options['sceneFilter']['cloudCoverFilter'] = kwargs['cloudCoverFilter']
            else:
                options['sceneFilter']['cloudCoverFilter'] = dict(
                    min=0,
                    max=kwargs.get('cloud_cover', 100),
                    includeUnknown=True
                )

            if 'bbox' in kwargs and kwargs['bbox'] is not None:
                bbox = kwargs['bbox']
                options['sceneFilter']['spatialFilter'] = dict(
                    filterType='mbr',
                    lowerLeft=dict(latitude=bbox[1], longitude=bbox[0]),
                    upperRight=dict(latitude=bbox[3], longitude=bbox[2]),
                )
            elif kwargs.get('filename') or kwargs.get('scene_id'):
                scene_id = kwargs.get('filename') or kwargs.get('scene_id')

                filter_name = self._get_filter(dataset=query, context='scene')

                criteria = self._criteria(scene_id.replace('*', ''), field_id=filter_name)
                options['sceneFilter']['metadataFilter'] = criteria
            elif kwargs.get('tile'):
                if query.lower().startswith('landsat'):
                    path, row = kwargs['tile'][:3], kwargs['tile'][-3:]
                elif query.lower().startswith('modis'):
                    path, row = kwargs['tile'][1:3], kwargs['tile'][-2:]

                path_filter = self._get_filter(dataset=query, context='path')
                row_filter = self._get_filter(dataset=query, context='row')

                path_criteria = self._criteria(int(path), filter_type='between',
                                               field_id=path_filter, secondValue=int(path))

                row_criteria = self._criteria(int(row), filter_type='between',
                                              field_id=row_filter, secondValue=int(row))

                options['sceneFilter']['metadataFilter'] = dict(
                    filterType='and',
                    childFilters=[path_criteria, row_criteria]
                )

        results = self.api.search(**options)

        valid_scene = self._valid_scene

        if 'validate' in kwargs:
            valid_scene = kwargs['validate']

            if not callable(valid_scene):
                raise ValueError(f'Invalid validate. Expected a callable(scene:dict), but got {valid_scene}')

        return [
            SceneResult(scene['displayId'], scene['cloudCover'], **scene)
            for scene in results if valid_scene(scene, dataset=query)
        ]

    def _valid_scene(self, scene: dict, dataset=None) -> bool:
        """Filter validator for invalid scenes.

        Sometimes, the USGS Catalog returns wrong scene_ids and this functions removes that holes.
        """
        # Only validate scene for Landsat products
        if dataset and not dataset.lower().startswith('landsat'):
            return True

        if scene['displayId'].endswith('RT') or scene['displayId'].startswith('LO08'):
            return False

        bounds_geom = shape(scene['spatialBounds'])
        xmin, ymin, xmax, ymax = bounds_geom.bounds

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

        id_field = kwargs.get('idFilter', 'displayId')

        if scene_id.startswith('LGN'):
            id_field = 'entityId'

        data_set = kwargs['dataset']

        try:
            looks = self.api.lookup(data_set, entity_ids=[scene_id], field_id=id_field)

            entity_id = looks[0]['entityId']

            meta = self.api.get_data_set_meta(data_set_name=data_set)

            resolver = get_resolver(data_set)

            file_name = self.ee.download(meta['datasetId'], entity_id, destination, link_resolver=resolver)

            return file_name
        except Exception as e:
            raise DownloadError(str(e))

    def disconnect(self):
        """Disconnect from the USGS server."""
        self.api.logout()
        self.ee.logout()
