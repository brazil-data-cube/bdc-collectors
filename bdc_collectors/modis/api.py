#
# This file is part of BDC-Collectors.
# Copyright (C) 2020 INPE.
#
# BDC-Collectors is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Define the API to communicate with NASA Download Data Server."""

import concurrent.futures
import os
import shutil
from operator import itemgetter
from tempfile import TemporaryDirectory

import pymodis
import shapely.geometry

from ..base import BaseProvider, SceneResult, SceneResults
from .parser import ModisScene

CATALOG_SEARCH_MAX_WORKERS = int(os.getenv('CATALOG_SEARCH_MAX_WORKERS', 4))
META_PROPERTIES = [
    'DayNightFlag', 'QAPercentCloudCover', 'PlatformShortName',
    'FileSize', 'ChecksumType', 'Checksum', 'ChecksumOrigin',
    'RangeBeginningDate', 'RangeEndingDate', 'LocalVersionID',
    'GranuleUR'
]


class ModisAPI(BaseProvider):
    """Represent an abstraction of how to iterate with NASA MODIS API."""

    def __init__(self, username, password, **kwargs):
        """Build a new object API."""
        self._auth = username, password
        self._kwargs = kwargs

        if kwargs.get('directory'):
            self.directory = kwargs['directory']
        else:
            self._tmp = kwargs.get('directory', TemporaryDirectory())
            self.directory = self._tmp.name

    def search(self, query, *args, **kwargs) -> SceneResults:
        """Search for MODIS product on NASA Catalog."""
        options = dict(
            product=query
        )

        if kwargs.get('start_date'):
            options['today'] = kwargs['start_date']

        if kwargs.get('end_date'):
            options['enddate'] = kwargs['end_date']

        if kwargs.get('tile'):
            options['tiles'] = kwargs['tile']

        if kwargs.get('filename') or kwargs.get('scene_id'):
            entry = kwargs.get('filename', kwargs.get('scene_id', ''))
            entry = entry.replace('.hdf', '').replace('.xml', '')

            scene = ModisScene(entry)

            options['today'] = scene.sensing_date().strftime('%Y-%m-%d')
            options['tiles'] = scene.tile_id()
            # The end date should be the same as today.
            options['enddate'] = options['today']

        # TODO: Implement way to deal with minimum bounding region
        api = self._get_client(**options)

        dates = api.getListDays()

        scenes = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=CATALOG_SEARCH_MAX_WORKERS) as executor:
            tasks = []
            for date in dates:
                tasks.append(executor.submit(self._search, date, api, **options))

            for task in concurrent.futures.as_completed(tasks):
                if not task.exception() and task.result():
                    result = task.result()

                    scenes.extend(result)

        return sorted(scenes, key=itemgetter('scene_id'))

    def download(self, scene_id: str, *args, **kwargs) -> str:
        """Download the MODIS product from NASA.

        Args:
            scene_id - The MODIS Scene identifier
            *args - List of optional parameters
            **kwargs - Extra parameters used to download
        """
        dataset = self._guess_dataset(scene_id, **kwargs)
        scene = self.search(dataset, scene_id=scene_id)[0]
        output = kwargs.get('output')

        parse = ModisScene(scene.scene_id)

        options = dict(
            today=parse.sensing_date().strftime('%Y-%m-%d'),
            tiles=parse.tile_id(),
            product=dataset
        )
        options['enddate'] = options['today']

        if output:
            os.makedirs(output, exist_ok=True)

        api = self._get_client(**options)

        api.downloadsAllDay()

        downloaded_file = os.path.join(self.directory, f'{scene.scene_id}.hdf')

        if output:
            output_file = os.path.join(output, os.path.basename(downloaded_file))
            if os.path.exists(output_file):
                os.remove(output_file)

            shutil.move(downloaded_file, output_file)
            downloaded_file = output_file

        return downloaded_file

    def _get_client(self, **options):
        options.setdefault('user', self._auth[0])
        options.setdefault('password', self._auth[1])

        api = pymodis.downmodis.downModis(self.directory, **options)
        api.connect()

        return api

    def _guess_dataset(self, scene_id, **kwargs):
        """Try to identify the MODIS from a sceneid.

        TODO: Improve this function.
        """
        scene = ModisScene(scene_id)

        return f'{scene.source()}.{scene.version()}'

    def _search(self, date_reference, api: pymodis.downmodis.downModis, **kwargs):
        files = api.getFilesList(date_reference)

        scenes = []

        for file in files:
            if file.endswith('.hdf'):
                scene = os.path.splitext(file)[0]
                file_xml = f'{file}.xml'
                # Download metadata file
                api.dayDownload(date_reference, [file_xml])

                downloaded_meta_file = f'{api.writeFilePath}/{file_xml}'
                meta = self._read_meta(downloaded_meta_file)
                link = f'{api.url}/{api.path}/{date_reference}/{file}'

                scenes.append(
                    SceneResult(scene, cloud_cover=float(meta['QAPercentCloudCover']), link=link, **meta)
                )

        return scenes

    def _read_meta(self, meta_file: str):
        from xml.etree import ElementTree

        tree = ElementTree.parse(str(meta_file))
        root = tree.getroot()

        meta = dict()

        for prop in META_PROPERTIES:
            value = None

            for element in root.findall(f'.//{prop}'):
                value = element.text
                break

            meta[prop] = value

        points = []
        for point_element in root.findall('.//Point'):
            long = point_element.find('PointLongitude').text
            lat = point_element.find('PointLatitude').text
            points.append((float(long), float(lat)))

        footprint_linear_ring = shapely.geometry.LinearRing(points)
        geom = shapely.geometry.Polygon(footprint_linear_ring)

        meta['geometry'] = shapely.geometry.mapping(geom)

        return meta
