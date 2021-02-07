#
# This file is part of BDC-Collectors.
# Copyright (C) 2020 INPE.
#
# BDC-Collectors is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Define the structures for USGS Earth Explorer Provider access."""

import os
import re
from json.decoder import JSONDecodeError
from random import randint
from typing import Any, Callable, List, Optional, Dict

import bs4
import requests

from ..exceptions import DownloadError
from ..utils import download_stream
from ._collections import default_download_resolver


class LandsatApi:
    """Define minimal API abstraction of USGS Server.

    This interface follows the `JSON API 1.5 <https://m2m.cr.usgs.gov/api/docs/json/>`_ stable spec.

    Use this API directly only if you really need. Otherwise use `bdc_collectors.usgs.USGS` instead.
    """

    api_url: str = 'https://m2m.cr.usgs.gov/api/api/json/{version}'

    session: requests.Session

    _filters: Dict[str, Any]

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
        self._filters = dict()

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

    def search(self, **kwargs):
        """Search for any data set on USGS.

        TODO:
            Implement data types like "sceneFilter", "metadataFilter", etc to improve usability.
        """
        data = self.request(f'{self.api_url}/scene-search', **kwargs)

        return data['results']

    def filters(self, dataset: str) -> List[Any]:
        """Retrieve all supported filters for a given data set."""
        if dataset not in self._filters:
            data = self.request(f'{self.api_url}/dataset-filters', datasetName=dataset)

            self._filters[dataset] = data

        return self._filters[dataset]

    def get_data_set_meta(self, data_set_id: Optional[str] = None, data_set_name: Optional[str] = None):
        """Retrieve the metadata of a data set."""
        options = dict()

        if data_set_id:
            options['datasetId'] = data_set_id
        if data_set_name:
            options['datasetName'] = data_set_name

        response = self.request(f'{self.api_url}/dataset', **options)

        return response

    def lookup(self, data_set_name: str, entity_ids: List[str], field_id: str = 'displayId', **kwargs):
        """Try to resolve a data set scene into entity id.

        This method wraps the USGS `scene-list-add` to add into context
        and the resource `scene-list-get`.
        """
        options = dict(
            datasetName=data_set_name,
            entityIds=entity_ids,
            idField=field_id,
            **kwargs
        )
        if 'listId' not in options:
            options['listId'] = f'the_list_{randint(1, 1000)}'
        options.setdefault('timeToLive', 'PT10S')

        _ = self.request(f'{self.api_url}/scene-list-add', **options)

        response = self.request(f'{self.api_url}/scene-list-get', listId=options['listId'])

        return response

    def download_options(self, data_set_name: str, entity_ids: List[str]):
        """Try to get the download link options."""
        response = self.request(f'{self.api_url}/download-options', datasetName=data_set_name, entityIds=entity_ids)

        return response


class EarthExplorer:
    """Represent an interface to communicate with Earth Explorer server and then download data from portal."""

    def __init__(self, username: str, password: str):
        """Build the class instance."""
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.login(self.username, self.password)

    def login(self, username: str, password: str):
        """Try to login in the EarthExplorer platform.

        In order to login in EarthExplorer, this method simulates a request.Session and
        authenticate using HTML parser.
        Once login worked, the session is kept until method `logout()` is invoked.

        Notes:
            This method may changes when there is update on USGS platform.
            Make sure to call `logout()` before terminate the application since there API Rate limit on platform.
        """
        _login_url = 'https://ers.cr.usgs.gov/login/'
        # Get HTML form information
        response = self.session.get(_login_url)
        # Parse the Login Form and retrieve CSRF_TOKEN and Form Secret
        form_secret, csrf_token = self._get_login_html_form_info(response.text)

        body_data = dict(
            username=username,
            password=password,
            csrf=csrf_token,
            __ncforminfo=form_secret
        )
        # Authenticate the user into request Session and keep it open
        _ = self.session.post(_login_url, data=body_data, allow_redirects=True)

        if not self.authenticated:
            raise RuntimeError('Could not login into EarthExplorer platform.')

    @property
    def authenticated(self):
        """Check if the log-in has been successfully based on session cookies."""
        eros_sso = self.session.cookies.get("EROS_SSO_production_secure")
        return bool(eros_sso)

    def _get_login_html_form_info(self, html: str):
        form_secret = re.findall(r'name="__ncforminfo" value="(.+?)"', html)[0]
        csrf_token = re.findall(r'name="csrf" value="(.+?)"', html)[0]

        if not form_secret and not csrf_token:
            raise RuntimeError('Missing "csrf"/"nc_form" property in login page. Is EarthExplorer online?')

        return form_secret, csrf_token

    def download(self, product_id: str, entity_id: str, output: str, link_resolver: Callable[[Any], str] = None) -> str:
        """Download data from USGS Server.

        Args:
            product_id (str): Internal data set product identifier. Check :func:`~LandsatApi.get_data_set_meta`.
            entity_id (str): Data set entity identifier.
            output (str): Path to download data.
            link_resolver (Callable[[Any], str]): Function to retrieve the download link from download options page.
                This function parses the EarthExplorer download options modal. By default, it get the download link
                url from the bottom.

        TODO: Implement link_resolver to the other supported collections.It only supports Landsat collections.
        """
        response = self.session.get(f'https://earthexplorer.usgs.gov/scene/downloadoptions/{product_id}/{entity_id}',
                                    timeout=90)

        if response.status_code != 200:
            raise DownloadError(f'Download Error - Could not get download options for {entity_id}.')

        # Passing "features" to get through warning.
        soup = bs4.BeautifulSoup(response.content, features='html.parser')

        if link_resolver is None:
            link_resolver = default_download_resolver

        product_id = link_resolver(soup)

        response = self.session.get(f'https://earthexplorer.usgs.gov/download/{product_id}/{entity_id}/EE',
                                    timeout=90, stream=True)

        local_filename = response.headers['Content-Disposition'].split('=')[-1]
        local_filename = local_filename.replace("\"", "")

        file_path = os.path.join(output, local_filename)

        download_stream(file_path, response)

        return file_path

    def logout(self):
        """Log out from Earth Explorer."""
        _ = self.session.get('https://earthexplorer.usgs.gov/logout')
