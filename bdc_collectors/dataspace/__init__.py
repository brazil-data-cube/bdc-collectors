import logging
import os
import shutil
import typing as t
from urllib.parse import ParseResult, urlparse

import requests

from .utils import get_access_token
from ..base import BaseProvider, SceneResults, BulkDownloadResult, SceneResult
from .stac import StacStrategy
from ..utils import download_stream


def init_provider():
    """Register the Copernicus Dataspace provider.

    Note:
        Called once by ``CollectorExtension``.
    """
    return dict(
        Dataspace=DataspaceProvider
    )


class DataspaceProvider(BaseProvider):
    session: requests.Session

    def __init__(self, username: str, password: str, strategy: t.Optional[BaseProvider] = None, **kwargs):
        self._kwargs = kwargs
        if strategy is None:
            default_options = {k: v for k, v in kwargs.items() if k.startswith("stac_")}
            strategy = StacStrategy(**default_options)
        self.strategy = strategy
        self.username = username
        self.password = password
        self.session = kwargs.get("session", requests.session())

    def search(self, query, *args, **kwargs) -> SceneResults:
        entries = self.strategy.search(query, *args, **kwargs)
        return entries

    def download(self, query, output: str, *args, **kwargs) -> SceneResults:
        if not isinstance(query, SceneResult):
            item_ids = kwargs.get("ids", [])
            if kwargs.get("sceneid") or kwargs.get("scene_id"):
                scene: str = kwargs.get("sceneid", kwargs.get("scene_id"))
                if not scene.endswith(".SAFE"):
                    scene = f"{scene}.SAFE"
                item_ids.append(scene)

            entries = self.strategy.search(query, ids=item_ids)
            if len(entries) == 0:
                raise RuntimeError(f"No product found to download using {query} and {item_ids}")
            query = entries[0]

        # Temporary workaround:
        # It seems like catalogue.dataspace.copernicus.eu is not being resolved
        # through Python requests library.
        # Using zipper.dataspace instead
        parsed: ParseResult = urlparse(query.link)
        parsed_changed = parsed._replace(netloc="zipper.dataspace.copernicus.eu")

        download_url = parsed_changed.geturl()

        token = get_access_token(self.username, self.password)  # TODO: Retrieve values from self._kwargs
        headers = {"Authorization": f"Bearer {token}"}
        self.session.headers = headers
        response = self.session.get(download_url, stream=True, timeout=600, allow_redirects=True)
        tmp_file = f"/tmp/{query.scene_id}.zip"
        target_file = os.path.join(output, f"{query.scene_id}.zip")
        os.makedirs(os.path.dirname(target_file), exist_ok=True)

        download_stream(tmp_file, response)

        shutil.move(tmp_file, target_file)

    def download_all(self, scenes: t.List[SceneResult], output: str, **kwargs) -> BulkDownloadResult:
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