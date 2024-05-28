#
# This file is part of Brazil Data Cube BDC-Collectors.
# Copyright (C) 2022 INPE.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/gpl-3.0.html>.
#

"""Define the API to communicate with NASA Download Data Server."""

import concurrent.futures
import os
import shutil
from datetime import date, datetime
from operator import itemgetter
from tempfile import TemporaryDirectory
from typing import Type

import shapely.geometry

from ..base import BaseCollection, BaseProvider, SceneResult, SceneResults
from ..exceptions import DataOfflineError
from ..utils import to_geom
from .collection import ModisCollection
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

        self.collections['MOD13Q1.006'] = ModisCollection
        self.collections['MYD13Q1.006'] = ModisCollection

    def get_collector(self, collection: str) -> Type[BaseCollection]:
        """Represent the structure to deal with Provider API."""
        return ModisCollection

    def search(self, query, *args, **kwargs) -> SceneResults:
        """Search for MODIS product on NASA Catalog."""
        options = dict(
            product=query
        )
        client_opts = self._kwargs.get("client_options", {})
        options.update(client_opts)

        path = kwargs.get('path')
        if path is None:
            path = self._guess_path(query)
        options['path'] = path

        if kwargs.get('start_date'):
            options['today'] = self._parse_date(kwargs['start_date']).strftime('%Y-%m-%d')

        if kwargs.get('end_date'):
            options['enddate'] = self._parse_date(kwargs['end_date']).strftime('%Y-%m-%d')

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

        api = self._get_client(**options)

        if kwargs.get("bbox"):
            options["geom"] = shapely.geometry.box(*kwargs["bbox"])

        if kwargs.get("geom"):
            options["geom"] = to_geom(kwargs["geom"])

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
        path = self._guess_path(dataset)
        scene = self.search(dataset, scene_id=scene_id)[0]
        output = kwargs.get('output')

        parse = ModisScene(scene.scene_id)

        options = dict(
            today=parse.sensing_date().strftime('%Y-%m-%d'),
            tiles=parse.tile_id(),
            product=dataset,
            path=path
        )
        options['enddate'] = options['today']

        if output:
            os.makedirs(output, exist_ok=True)

        api = self._get_client(**options)

        try:
            api.downloadsAllDay()
        except AttributeError:
            # Aborted connection by remote server. In this case, raise a DataOfflineError
            # to make 3rdparty library identify
            raise DataOfflineError(scene_id)

        downloaded_file = os.path.join(self.directory, f'{scene.scene_id}.hdf')

        if output:
            output_file = os.path.join(output, os.path.basename(downloaded_file))
            if os.path.exists(output_file):
                os.remove(output_file)

            shutil.move(downloaded_file, output_file)
            downloaded_file = output_file

        return downloaded_file

    def _parse_date(self, dt) -> date:
        if isinstance(dt, str):
            return datetime.fromisoformat(dt).date()
        elif isinstance(dt, datetime):
            return dt.date()
        elif isinstance(dt, date):
            return dt
        raise TypeError('Invalid date')

    def _get_client(self, **options):
        import pymodis

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

    def _guess_path(self, dataset: str):
        """Try to identify remote server path prefix according to data set information.

        TODO: We should list all entries and filter on remote host.
        """
        if dataset.startswith('MYD'):
            return 'MOLA'
        if dataset.startswith('MOD'):
            return 'MOLT'
        if dataset.startswith('MCD'):
            return 'MOTA'
        if dataset.startswith('VNP'):
            return 'VIIRS'
        raise RuntimeError(f'Dataset {dataset} not supported.')

    def _search(self, date_reference, api, **kwargs):
        files = api.getFilesList(date_reference)

        scenes = []
        geom = kwargs.get("geom")

        for file in files:
            if file.endswith('.hdf'):
                scene = os.path.splitext(file)[0]
                file_xml = f'{file}.xml'
                # Download metadata file
                api.dayDownload(date_reference, [file_xml])

                downloaded_meta_file = f'{api.writeFilePath}/{file_xml}'
                meta = self._read_meta(downloaded_meta_file)

                if geom is not None and meta.get("geometry"):
                    g = shapely.geometry.shape(meta["geometry"])
                    if not g.intersects(geom):
                        continue

                link = f'{api.url}/{api.path}/{date_reference}/{file}'

                scenes.append(
                    SceneResult(scene, cloud_cover=float(meta['QAPercentCloudCover']) if meta['QAPercentCloudCover'] else None, link=link, **meta)
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
