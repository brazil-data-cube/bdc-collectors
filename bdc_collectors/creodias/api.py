#
# This file is part of BDC-Collectors.
# Copyright (C) 2020 INPE.
#
# BDC-Collectors is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Define the API class for communication with CREODIAS server."""

import os
from datetime import datetime
from typing import Dict, List, Optional, Union

import dateutil.parser
import requests

from ..base import SceneResult
from ..utils import download_stream

DateT = Union[str, datetime]
Link = Dict[str, str]


class Api:
    """Define simple abstraction of CREODIAS API."""

    url: str = 'http://finder.creodias.eu/resto/api/collections/{collection}/search.json?maxRecords=500'
    auth_url: str = 'https://auth.creodias.eu/auth/realms/DIAS/protocol/openid-connect/token'

    def __init__(self, username, password, progress=False):
        """Create CREODIAS API instance."""
        self.username = username
        self.password = password
        self.progress = progress

    @property
    def access_token(self):
        """Retrieve the user access token."""
        params = dict(
            username=self.username,
            password=self.password,
            client_id='CLOUDFERRO_PUBLIC',
            grant_type='password'
        )

        response = requests.post(self.auth_url, data=params)

        if response.status_code != 200:
            raise RuntimeError('Unauthorized.')

        return response.json()['access_token']

    def search(self, collection: str, start_date: Optional[DateT] = None, end_date: Optional[DateT] = None,
               geom: str = None, status: str = 'all', **kwargs) -> List[SceneResult]:
        """Search for data products in ONDA catalog.

        Args:
            collection - The collections defined by ONDA provider.
                The following values are supported:
                Sentinel1, Sentinel2, Sentinel3, Sentinel5P,Landsat8,Landsat7,Landsat5 and EnvSat
            start_date - The sensing date
            end_date - The end date of the observation.
            geom - Area in WKT
            **kwargs - The others parameters for request.
                The supported parameters are defined in `EO Data Finder API Manual <https://creodias.eu/eo-data-finder-api-manual>`_.

        Returns:
            The list of matched scenes.
        """
        url = self.url.format(collection=collection)

        params = dict(**kwargs)

        if geom:
            params['geometry'] = geom

        if status:
            params['status'] = status

        if start_date:
            params['startDate'] = self._parse_date(start_date).isoformat()

        if end_date:
            params['completionDate'] = self._parse_date(end_date).isoformat()

        result = []

        while url is not None:
            response = requests.get(url, params=params)

            content = response.json()

            for feature in content['features']:
                scene_id = feature['properties']['title'].replace('.SAFE', '')
                cloud_cover = feature['properties']['cloudCover']

                link = ''

                if feature['properties']['services']:
                    link = feature['properties']['services']['download']

                result.append(SceneResult(scene_id, cloud_cover, link=link, **feature))

            url = self._next_page(content['properties']['links'])

        return result

    @staticmethod
    def _next_page(links: List[Link]):
        """Seek for next page in query result links."""
        for link in links:
            if link['rel'] == 'next':
                return link['href']

        return None

    @staticmethod
    def _parse_date(date: DateT) -> datetime:
        """Try to parse a value to date."""
        if isinstance(date, datetime):
            return date

        return dateutil.parser.isoparse(date)

    def download(self, scene: SceneResult, output: str, max_retry: int = 10, force: bool = False) -> str:
        """Download the scene of CREODIAS server.

        Notes:
            We cant resume download since the CREODIAS given file size does not match with downloaded file.
        """
        access_token = self.access_token
        uuid = scene['id']
        # TODO: Get download_url from scene['properties']['servives']['download']. Check scene availability (status)

        download_url = f'https://zipper.creodias.eu/download/{uuid}?token={access_token}'

        tmp_file = f'{output}.incomplete'

        headers = dict()

        # HEAD Server to get file size
        head = requests.head(download_url, timeout=90)

        def _remove_file_if_exists(file_path):
            if os.path.exists(file_path) and os.path.isfile(file_path):
                os.remove(file_path)

        with head:
            expected_file_size = int(head.headers.get('Content-Length', 0))

        # Force download ??
        if force:
            _remove_file_if_exists(tmp_file)
        else:
            output_file_size = os.stat(output).st_size if os.path.exists(output) else 0

            if output_file_size > 0 and output_file_size == expected_file_size:
                # File has same byte size.
                # TODO: Should we validate before??
                return output

        # Get current size of temporary file
        tmp_file_size = os.stat(tmp_file).st_size if os.path.exists(tmp_file) else 0

        for retry in range(max_retry):
            if tmp_file_size > 0:
                if tmp_file_size > expected_file_size:
                    # file large than expected.
                    _remove_file_if_exists(tmp_file)
                if tmp_file_size == expected_file_size:
                    break

                headers['Range'] = f'bytes={tmp_file_size}-'

            response = requests.get(download_url, stream=True, timeout=90, headers=headers)

            download_stream(tmp_file, response, progress=self.progress, offset=tmp_file_size, total_size=expected_file_size)

            tmp_file_size = os.stat(tmp_file).st_size

            if tmp_file_size > 0 and tmp_file_size == expected_file_size:
                break

            if retry == max_retry - 1:
                raise DownloadError(f'Download error - Max retry exceeded for {scene.scene_id}.')

        _remove_file_if_exists(output)

        os.rename(tmp_file, output)

        return output
