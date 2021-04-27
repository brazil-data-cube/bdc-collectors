#
# This file is part of BDC-Collectors.
# Copyright (C) 2020 INPE.
#
# BDC-Collectors is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Defines the structures for Google Provider access."""

import logging
import os
import shutil
from pathlib import Path

from google.cloud import storage

from ..base import BaseProvider
from ..scihub.sentinel2 import Sentinel2
from ..usgs.landsat5 import Landsat5
from ..usgs.landsat7 import Landsat7
from ..usgs.landsat8 import Landsat8
from ..utils import working_directory
from .landsat import GoogleLandsat
from .sentinel import GoogleSentinel


def init_provider():
    """Register the provider Google."""
    # TODO: Register in bdc_catalog.models.Provider

    return dict(
        Google=Google
    )


class Google(BaseProvider):
    """Google provider definition.

    This providers consumes the `Google Public Data Sets <https://cloud.google.com/storage/docs/public-datasets>`_

    Currently, we support both `Sentinel-2` and `Landsat` products.

    Note:
        This provider requires `GOOGLE_APPLICATION_CREDENTIALS` to work properly.
        Make sure to set in terminal or pass as variable in constructor.
    """

    storage_client: storage.Client

    def __init__(self, **kwargs):
        """Create instance of Google Provider."""
        credentials = kwargs.get('GOOGLE_APPLICATION_CREDENTIALS')

        if credentials is None:
            credentials = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

            if credentials is None:
                raise RuntimeError('The Google Provider requires env GOOGLE_APPLICATION_CREDENTIALS')

        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials

        self.storage_client = storage.Client()

        # Attaching collections to be accessed and get local directory structure
        self.collections['LANDSAT_5'] = Landsat5
        self.collections['LANDSAT_7'] = Landsat7
        self.collections['LANDSAT_8'] = Landsat8
        self.collections['LANDSAT_8'] = Landsat8
        self.collections['Sentinel-2'] = Sentinel2

    def search(self, query, *args, **kwargs):
        """Search for data set in Google Provider.

        Currently, it is not supported yet, since requires to download large `.csv` to check.

        TODO: Implement way to download and keep up to dated the `.csv` file.
        """
        # TODO: read .csv???
        raise RuntimeError('Search is not supported for this provider')

    def download(self, scene_id: str, *args, **kwargs):
        """Download scene from Google buckets."""
        try:
            # Creates a GCS Client
            storage_client = storage.Client()

            destination = kwargs.get('output')

            data_handler = guess_scene_parser(scene_id)

            bucket = storage_client.bucket(data_handler.bucket)

            blob_name = Path(data_handler.get_url())

            folder = data_handler.folder

            blobs = list(bucket.list_blobs(prefix=str(blob_name)))

            if len(blobs) == 0:
                raise RuntimeError('Scene {} not found on Google Cloud Storage.'.format(scene_id))

            downloaded_files = []

            for blob in blobs:
                blob_path = Path(blob.name)

                if blob.name.endswith(f'{folder}_$folder$'):
                    continue

                blob_relative = blob_path.relative_to(blob_name)

                target_path = Path(destination) / folder / str(blob_relative)
                target_path.parent.mkdir(parents=True, exist_ok=True)

                if str(blob_path).endswith('$folder$'):
                    continue

                blob.download_to_filename(str(target_path))

                data_handler.apply_processing(target_path)

                downloaded_files.append(str(target_path))

            return data_handler.process(downloaded_files, destination)
        except Exception as e:
            logging.error(f'Could not download from Google {scene_id} - {str(e)}')


def guess_scene_parser(scene_id):
    """Try to identify a parser for Scene Id.

    Raises:
        RuntimeError when cant parse scene_id.

    Args:
        scene_id - Scene id product

    Returns:
        A Google Data Set
    """
    from ..scihub.parser import Sentinel2Scene
    from ..usgs.parser import LandsatScene

    parsers = [GoogleLandsat, GoogleSentinel]

    found = None

    for parser in parsers:
        try:
            found = parser(scene_id)
            break
        except RuntimeError:
            continue

    if found is None:
        raise RuntimeError('Cant guess parser')

    return found
