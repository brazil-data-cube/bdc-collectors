#
# This file is part of Brazil Data Cube BDC-Collectors.
# Copyright (C) 2023 INPE.
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

"""Define the implementation of Copernicus Dataspace Program.

This module is a new version of :class:`bdc_collectors.scihub.SciHub` (deprecated) to consume and download Sentinel products.
"""

import logging
import os
import shutil
import typing as t
from urllib.parse import ParseResult, urlparse

import requests

from ..base import BaseProvider, BulkDownloadResult, SceneResult, SceneResults
from ..exceptions import DataOfflineError
from ..scihub.sentinel2 import Sentinel1, Sentinel2
from ..utils import download_stream, import_entry
from ._token import TokenManager
from .odata import ODATAStrategy


def init_provider():
    """Register the Copernicus Dataspace provider.

    Note:
        Called once by ``CollectorExtension``.
    """
    return dict(
        Dataspace=DataspaceProvider
    )


class DataspaceProvider(BaseProvider):
    """Represent the Driver for Copernicus Dataspace program.
    
    This module supports the following API provider using strategies:
    - ODATA
    - STAC

    By default, the ODATAStrategy is used to search for Sentinel Data.
    For Authorization and Token Authentication, as defined in
    `Access Token <https://documentation.dataspace.copernicus.eu/APIs/Token.html>`_,
    an ``access_token`` is required to download data. By default, this module stores these tokens in
    :class:`bdc_collectors.dataspace._token.TokenManager`. Whenever a download is initiated by 
    :method:`bdc_collectors.dataspace.DataspaceProvider.download`, the bdc-collectors creates two (2) access tokens
    in memory and then use it to download as many scenes as can. When the token expires, it automatically refresh
    a new token.

    Examples:
        The following example consists in a minimal download scenes from Dataspace program using ODATA API

        >>> from bdc_collectors.dataspace import DataspaceProvider
        >>> provider = DataspaceProvider(username='user@email.com', password='passwd')
        >>> entries = provider.search('SENTINEL-2', bbox=(-54, -12, -50, -10), product="S2MSI2A")
        >>> for entry in entries:
        ...     provider.download(entry, output='sentinel-2')


        You may change the API backend with command:
        >>> from bdc_collectors.dataspace.stac import StacStrategy
        >>> stac = StacStrategy()
        >>> provider = DataspaceProvider(username='user@email.com', password='passwd', strategy=stac)
        >>> # or change directly in API
        >>> provider.strategy = stac
    """

    session: requests.Session

    def __init__(self, username: str, password: str, strategy: t.Optional[BaseProvider] = None, **kwargs):
        """Build a Dataspace provider instance."""
        self._kwargs = kwargs

        default_options = {k: v for k, v in kwargs.items() if k.startswith("stac_") or k.startswith("odata_")}

        if strategy is None:
            strategy = ODATAStrategy(**default_options)
        elif isinstance(strategy, str):
            strategy_cls: t.Type[BaseProvider] = import_entry(strategy)
            strategy = strategy_cls(**default_options)

        self.strategy = strategy
        # self.username = username
        # self.password = password
        self.session = kwargs.get("session", requests.session())
        self.collections = {
            "SENTINEL-1": Sentinel1,
            "SENTINEL-2": Sentinel2,
        }

        manager_options = {k: v for k, v in kwargs.items() if k.startswith("token_")}
        self._token_manager = TokenManager(username, password, redis_url=kwargs.get("redis_url"), **manager_options)

    def search(self, query, *args, **kwargs) -> SceneResults:
        """Search for data products in Copernicus Dataspace program."""
        entries = self.strategy.search(query, *args, **kwargs)
        return entries

    def download(self, query: t.Union[SceneResult, str], output: str, *args, **kwargs) -> str:
        """Download the specified item from API provider."""
        if not isinstance(query, SceneResult):
            item_ids = kwargs.get("ids", [])

            scene = ""
            if query.startswith("S2"):
                scene = query

            if kwargs.get("sceneid") or kwargs.get("scene_id"):
                scene: str = kwargs.get("sceneid", kwargs.get("scene_id"))

            if not scene.endswith(".SAFE"):
                scene = f"{scene}.SAFE"

            item_ids.append(scene)

            entries = self.strategy.search(query, ids=item_ids)
            if len(entries) == 0:
                raise RuntimeError(f"No product found to download using {query} and {item_ids}")
            query = entries[0]

        # ODATAStrategy only
        if "Online" in query and not query.get("Online"):
            raise DataOfflineError(query.scene_id)

        filename = f"{query.scene_id}.zip"
        target_file = os.path.join(output, filename)
        tmp_file = os.path.join(output, f"{filename}.incomplete")
        os.makedirs(output, exist_ok=True)

        # Temporary workaround:
        # It seems like catalogue.dataspace.copernicus.eu is not being resolved
        # through Python requests library.
        # Using zipper.dataspace instead
        parsed: ParseResult = urlparse(query.link)
        parsed_changed = parsed._replace(netloc="zipper.dataspace.copernicus.eu")

        download_url = parsed_changed.geturl()

        token = self._token_manager.get_token()

        headers = {"Authorization": f"Bearer {token.token}"}
        self.session.headers = headers
        response = self.session.get(download_url, stream=True, timeout=600, allow_redirects=True)

        # TODO: Validate Offline/Exception to retry later Checksum
        download_stream(tmp_file, response, progress=self._kwargs.get("progress", False))

        shutil.move(tmp_file, target_file)

        return target_file

    def download_all(self, scenes: t.List[SceneResult], output: str, **kwargs) -> BulkDownloadResult:
        """Download multiple scenes from remote Copernicus Dataspace program in bulk-mode."""
        failed = []
        success = []
        for scene in scenes:
            downloaded_file = self.download(scene, output=output, **kwargs)
            if downloaded_file is None:
                failed.append(scene.scene_id)
            else:
                success.append(scene.scene_id)

        return (success, [], failed,)


    def _download(self, entry: SceneResult, output: str, **kwargs):
        try:
            downloaded_file = self.download(entry, output=output, **kwargs)

            return downloaded_file
        except RuntimeError:
            logging.error(f"Scene not found {entry.scene_id}")
        except BaseException:
            logging.error(f"DownloadError for {entry.scene_id}")
        return None