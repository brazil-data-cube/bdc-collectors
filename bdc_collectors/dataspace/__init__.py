import typing as t

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
    def __init__(self, username: str, password: str, strategy: t.Optional[BaseProvider] = None, **kwargs):
        self._kwargs = kwargs
        if strategy is None:
            default_options = {k: v for k, v in kwargs.items() if k.startswith("stac_")}
            strategy = StacStrategy(**default_options)
        self.strategy = strategy
        self.username = username
        self.password = password

    def search(self, query, *args, **kwargs) -> SceneResults:
        entries = self.strategy.search(query, *args, **kwargs)
        return entries

    def download(self, query, *args, **kwargs) -> SceneResults:
        if not isinstance(query, SceneResult):
            ...

        token = get_access_token(self.username, self.password)  # TODO: Retrieve values from self._kwargs
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(query.link, headers=headers, timeout=90, stream=True)
        download_stream(f"/tmp/{query.scene_id}.zip", response)

    def download_all(self, scenes: t.List[SceneResult], output: str, **kwargs) -> BulkDownloadResult:
        ...
