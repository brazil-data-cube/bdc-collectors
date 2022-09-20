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

"""Download entire Sentinel-2 tile from remote server.

This example tries to download data from SciHub. When it fails,
seeks in CREODIAS (Requires BDC_CREODIAS_USER and BDC_CREODIAS_PASSWORD set).
"""

import logging
import os
import time
from datetime import datetime, timedelta
from logging.handlers import TimedRotatingFileHandler

import fiona

from bdc_collectors import CollectorExtension
from bdc_collectors.scihub.base import Sentinel2Scene
from bdc_collectors.exceptions import DownloadError
from flask import Flask


def setup_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    handler = TimedRotatingFileHandler(
        'application.log',
        when='D',
        backupCount=30
    )
    handler.suffix = '%Y%m%d%H%M'
    handler.setFormatter(formatter)

    logger.addHandler(stream_handler)
    logger.addHandler(handler)

    return logger

logger = setup_logger()

S2_GRID_DIR = os.getenv('SHP_DATA_DIR', './shp')
S2_GRID_NAME = os.getenv('SHP_FILENAME', 'grade_mgrs_s2_brasil.shp')
S2_GRID_FILE_NAME = os.path.join(S2_GRID_DIR, S2_GRID_NAME)

if not os.path.exists(S2_GRID_FILE_NAME):
    raise IOError('Sentinel grid shapefile not found')

# Sentinel
with fiona.open(S2_GRID_FILE_NAME) as dataset:
    TILES = [tile['properties']['name'] for tile in dataset.values()]

START_DATE = datetime.strptime(os.getenv('START_DATE', '2019-08-01'), '%Y-%m-%d')
END_DATE = datetime.strptime(os.getenv('END_DATE', '2019-08-31'), '%Y-%m-%d')
DELTA_DAYS = timedelta(days=int(os.getenv('DELTA_DAYS', 10)))
DATA_DIR = os.getenv('DATA_DIR', '/data')
current_date = START_DATE
USER = os.getenv('BDC_USER', 'user')
PASSWORD = os.getenv('BDC_PASSWORD', 'password')

# Flask
app = Flask(__name__)
ext = CollectorExtension(app)

# SciHub Copernicus - https://scihub.copernicus.eu/dhus/#/home
sentinel = ext.get_provider('SciHub')(username=USER, password=PASSWORD, progress=True)

creodias = None

if os.getenv('BDC_CREODIAS_USER') and os.getenv('BDC_CREODIAS_PASSWORD'):
    user = os.getenv('BDC_CREODIAS_USER')
    passwd = os.getenv('BDC_CREODIAS_PASSWORD')

    creodias = ext.get_provider('CREODIAS')(username=user, password=passwd, progress=True)


logger.info(f'Download is starting')

while current_date < END_DATE:
    for tile in TILES:
        tile_path = os.path.join(DATA_DIR, f'{tile}')

        os.makedirs(tile_path, exist_ok=True)

        try:
            result = sentinel.search(
                query='S2MSI1C',
                platform='Sentinel-2',
                date=(current_date, current_date + DELTA_DAYS),
                cloudcoverpercentage=(0, 100),
                filename=f'*{tile}*'
            )

            time.sleep(6)

            logger.info(f'Download: {tile} - {current_date}/{current_date + DELTA_DAYS}')

            uuid_scene_map = {item['uuid']: item for item in result}

            if len(uuid_scene_map) == 0:
                logger.warning(f'No result for {current_date} - {tile}')
                continue

            try:
                downloaded, scheduled, failed = sentinel.download_all(result, output=tile_path, lta_retry_delay=30)
            except:
                downloaded = scheduled = {}
                logger.error(f'Error in sentinel-sat {list(uuid_scene_map.keys())}')
                # Look for local filed already downloaded and then check file integrity.
                # TODO: Should we change .incomplete of CREODIAS to avoid byte conflict?
                error_map = sentinel.api.check_files(ids=list(uuid_scene_map.keys()), directory=tile_path)

                # Map invalid files by scene
                failed = {v[0]['id']: uuid_scene_map[v[0]['id']] for k, v in error_map.items()}

            if scheduled or failed:
                logger.info(f'{len(scheduled)} were scheduled by SciHub LTA and {len(failed)} failed.')
                if creodias:
                    total_errors = list(scheduled.keys()) + list(failed.keys())

                    # Adapt to SceneResult
                    scenes = [uuid_scene_map[uuid] for uuid in total_errors]

                    downloaded = []
                    failed = []
                    for scene in scenes:
                        try:
                            creodias.download(scene.scene_id, output=tile_path)
                            downloaded.append(scene)
                        except:
                            failed.append(scene)

                    logger.info(f'{len(downloaded)} were downloaded and {len(failed)} failed on creodias.')

                    # Download from creodias - In parallel like sentinel-sat api
                    # downloaded, scheduled, failed = creodias.download_all(scenes, output=tile_path, max_workers=2)

        except DownloadError as e:
            logger.error(str(e))
        except Exception as e:
            logger.error(f'Exception - {e}', exc_info=True)

    current_date += DELTA_DAYS
