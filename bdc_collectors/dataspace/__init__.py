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

import hashlib
import logging
import os
import shutil
import time
import typing as t
from pathlib import Path

import requests

from ..base import BaseProvider, BulkDownloadResult, SceneResult, SceneResults
from ..exceptions import DataOfflineError, DownloadError
from ..scihub.sentinel2 import Sentinel1, Sentinel2, Sentinel3
from ..utils import download_stream, import_entry, to_bool
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
    :meth:`bdc_collectors.dataspace.DataspaceProvider.download`, the bdc-collectors creates two (2) access tokens
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
        self.session = kwargs.get("session", requests.session())
        self.collections = {
            "SENTINEL-1": Sentinel1,
            "SENTINEL-2": Sentinel2,
            "SENTINEL-3": Sentinel3
        }

        manager_options = {k: v for k, v in kwargs.items() if k.startswith("token_")}
        self._token_manager = TokenManager(username, password, redis_url=kwargs.get("redis_url"), **manager_options)

    def search(self, query, *args, **kwargs) -> SceneResults:
        """Search for data products in Copernicus Dataspace program."""
        options = kwargs.copy()

        # Compatibility with others BDC-Providers
        scenes = []
        if options.get("scene"):
            scenes.append(self._item_id(options["scene"]))
        if options.get("scenes"):
            scenes.extend([self._item_id(scene) for scene in options["scenes"]])

        if options.get("filename"):
            scenes.append(self._item_id(options["filename"].replace("*", "")))

        if scenes:
            options.setdefault("ids", [])
            options["ids"].extend(scenes)

        entries = self.strategy.search(query, *args, **options)
        return entries

    def download(self, query: t.Union[SceneResult, str], output: str, *args, **kwargs) -> str:
        """Download the specified item from API provider."""
        if not isinstance(query, SceneResult):
            item_ids = kwargs.get("ids", [])

            scene = query

            if kwargs.get("sceneid") or kwargs.get("scene_id"):
                scene: str = kwargs.get("sceneid", kwargs.get("scene_id"))

            scene = self._item_id(scene)

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

        if self._check_integrity(query, target_file):
            return target_file

        if self._check_integrity(query, tmp_file):
            shutil.move(tmp_file, target_file)
            return target_file

        response = self.session.get(query.link, allow_redirects=False)

        download_url = query.link

        while response.status_code in (301, 302, 303, 307):
            download_url = response.headers["Location"]
            response = self.session.get(download_url, allow_redirects=False)

        # Retry 3 times before reject
        for i in range(3):
            token = self._token_manager.get_token()

            headers = {"Authorization": f"Bearer {token.token}"}
            self.session.headers = headers
            try:
                response = self.session.get(download_url, stream=True, timeout=600, allow_redirects=True)

                # TODO: Validate Offline/Exception to retry later Checksum
                download_stream(tmp_file, response, progress=self._kwargs.get("progress", False))

                if self._check_integrity(query, tmp_file):
                    break

            except Exception:
                logging.debug(f"Error in download {query.scene_id}")
                time.sleep(3)

            if i == 2:
                raise DownloadError(f"Could not download {query.scene_id}")

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

    def _check_integrity(self, scene: SceneResult, filepath: str):
        """Check for scene file integrity if exists.

        Note:
            Ensure that the file is writable.
            It removes the file when its invalid.
        """
        if not os.path.exists(filepath):
            return False

        skip_checksum = to_bool(os.getenv("SKIP_CHECKSUM", "0"))
        if skip_checksum:
            res = is_valid_zip(filepath)

            logging.info(f"Testing zip (unzip -t) {filepath} {res}")
            return res

        if scene.get("Checksum"):
            checksums = scene["Checksum"]
            if not _is_valid_checksum(filepath, checksums):
                os.unlink(filepath)

                return False

        # TODO: Consider scene.get("ContentLength")??
        return True

    def _item_id(self, scene: str) -> str:
        if not scene.endswith(".SAFE") and scene[:2] in ("S1", "S2"):
            return f"{scene}.SAFE"
        elif not scene.endswith(".SEN3") and scene[:2] in ("S3",):
            return f"{scene}.SEN3"
        return scene


def _is_valid_checksum(filepath: str, checksums: t.List[t.Dict[str, t.Any]]) -> bool:
    """Assert checksum validity of data."""
    for context in checksums:
        algorithm_name = context["Algorithm"]
        algorithm_cls = getattr(hashlib, algorithm_name.lower(), None)
        if not algorithm_cls:
            logging.debug(f"No support for checksum algorithm {algorithm_name}, skipping.")
            continue

        algorithm = algorithm_cls()
        checksum = _check_sum(filepath, algorithm)
        if checksum == context["Value"]:
            return True

        logging.warning(f"Checksum error {context['Value']}, got {checksum}")

    return False


def _check_sum(file_path: t.Union[str, t.Any], algorithm: t.Any, chunk_size=16384) -> bytes:
    """Read a file and generate a checksum.

    Raises:
        IOError when could not open given file.

    Args:
        file_path (str|BytesIo): Path to the file
        algorithm (hashlib.Hash): A python hashlib algorithm.
        chunk_size (int): Size in bytes to read per iteration. Default is 16384 (16KB).

    Returns:
        The hex digest.
    """

    def _read(stream):
        for chunk in iter(lambda: stream.read(chunk_size), b""):
            algorithm.update(chunk)

    if isinstance(file_path, str) or isinstance(file_path, Path):
        with open(str(file_path), "rb") as f:
            _read(f)
    else:
        _read(file_path)

    return algorithm.hexdigest()


def is_valid_zip(filepath: str) -> bool:
    """Check the consistency of Zip file."""
    import subprocess

    proc = subprocess.Popen(["unzip", "-t", filepath], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    proc.wait()

    return proc.returncode == 0
