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

"""Simple implementation of ONDA Catalogue."""

from pathlib import Path

import requests

from ..utils import download_stream


class Api:
    """Define a simple abstraction of ONDA catalog."""

    URL = 'https://catalogue.onda-dias.eu/dias-catalogue/Products'

    username: str
    password: str

    def __init__(self, username=None, password=None, progress=True):
        """Create catalog instance."""
        self.username = username
        self.password = password
        self.progress = progress

    def order(self, product_id):
        """Order an offline product to ONDA Catalogue."""
        base_uri = '%s({})/Ens.Order' % self.URL

        auth = self.username, self.password

        headers = {
            'Content-Type': 'application/json'
        }

        req = requests.post(base_uri.format(product_id), timeout=90, auth=auth, headers=headers)

        req.raise_for_status()

    def download(self, scene_id: str, destination: str) -> str:
        """Try to download scene from ONDA Provider.

        Raises:
            Exception when scene is offline
            RuntimeError when scene not found.

        Note:
            The scene may not be available. In this case, you must order
            using "Api.order()". Make sure to set credentials.

        By default, when scene is offline, it will throw Exception.

        Args:
            destination: Path to store file
        """
        base_uri = '%s({})/$value' % self.URL

        meta = self.search_by_scene_id(scene_id)
        product_id = meta['id']

        auth = self.username, self.password

        destination = Path(str(destination)) / '{}.zip'.format(scene_id)

        req = requests.get(base_uri.format(product_id), stream=True, timeout=90, auth=auth)

        req.raise_for_status()

        download_stream(destination, req, progress=self.progress)

        return str(destination)

    def search(self, search, fmt='json') -> dict:
        """Search on ONDA Catalog."""
        query = {
            '$search': search,
            '$format': fmt
        }

        req = requests.get(self.URL, params=query, timeout=90)

        req.raise_for_status()

        content = req.json()

        return content

    def search_by_scene_id(self, scene_id: str) -> dict:
        """Search on ONDA Catalogue for Sentinel 2 by scene_id."""
        results = self.search('"name:{}.zip"'.format(scene_id))

        if len(results['value']) == 0:
            raise RuntimeError('{} not found.'.format(scene_id))

        return results['value'][0]
