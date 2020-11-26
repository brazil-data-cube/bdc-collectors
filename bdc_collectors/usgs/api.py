#
# This file is part of BDC-Collectors.
# Copyright (C) 2020 INPE.
#
# BDC-Collectors is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Define the structures for USGS Earth Explorer Provider access."""

from json.decoder import JSONDecodeError
from typing import Any, List, Optional

import requests


class LandsatApi:
    """Define minimal API abstraction of USGS Server.

    Use this API directly only if you really need. Otherwise use `bdc_collectors.usgs.USGS` instead.
    """

    api_url: str = 'https://m2m.cr.usgs.gov/api/api/json/{version}'

    session: requests.Session

    def __init__(self, username: str, password: str, version: str = 'stable',
                 lazy: bool = False, progress: bool = False, **kwargs):
        """Build a API instance."""
        self.api_url = self.api_url.format(version=version)
        self.session = requests.Session()
        self.session.headers.update(**{'Content-Type': 'application/json'})
        self._credentials = dict(
            username=username,
            password=password,
            **kwargs
        )
        self.progress = progress

        if not lazy:
            self.login()

    def login(self):
        """Connect to the remote USGS environment.

        Once logged in, it already appends the Access Token to the session.

        Raises:
            RuntimeError for any error occurred.
        """
        response = self.session.post(f'{self.api_url}/login', json=self._credentials,
                                     headers={'Content-Type': 'application/json'})

        # TODO: validate content type
        data = response.json()

        if response.status_code != 200 or data.get('errorCode'):
            raise RuntimeError(f'Error: {data["errorMessage"]}')

        self.session.headers.update({'X-Auth-Token': data['data']})

    def request(self, url: str, **parameters) -> Any:
        """Define a simple abstraction of request resource on USGS."""
        response = self.session.post(url, json=parameters)

        try:
            data = response.json()
        except JSONDecodeError as e:
            raise RuntimeError(f'Error: Cant parse USGS response as JSON. Got {response.content}')

        if data.get('errorMessage'):
            raise RuntimeError(f'Error: {data["errorMessage"]}')

        return data['data']

    def logout(self):
        """Logout the session.

        Remember to call before shutdown your application.
        """
        if self.session.headers.get('X-Auth-Token'):
            response = self.request(f'{self.api_url}/logout')
            print(response)

    def search(self, **kwargs):
        """Search for any data set on USGS.

        TODO:
            Implement data types like "sceneFilter", "metadataFilter", etc to improve usability.
        """
        data = self.request(f'{self.api_url}/scene-search', **kwargs)

        return data['results']

    def filters(self, dataset: str) -> List[Any]:
        """Retrieve all supported filters for a given data set."""
        data = self.request(f'{self.api_url}/dataset-filters', datasetName=dataset)

        return data

    def get_data_set_meta(self, data_set_id: Optional[str] = None, data_set_name: Optional[str] = None):
        """Retrieve the metadata of a data set."""
        options = dict()

        if data_set_id:
            options['datasetId'] = data_set_id
        if data_set_name:
            options['datasetName'] = data_set_name

        response = self.request(f'{self.api_url}/dataset', **options)

        return response

