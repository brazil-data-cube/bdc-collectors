import typing as t

from pystac_client import Client

from ..base import BaseProvider, SceneResults, SceneResult
from ..scihub.sentinel2 import Sentinel2


DEFAULT_STAC_URL: str = "https://catalogue.dataspace.copernicus.eu/stac"


class StacStrategy(BaseProvider):
    def __init__(self, stac_url: str = DEFAULT_STAC_URL, **kwargs):
        self.client = Client.open(stac_url, **kwargs)

    def collections_supported(self):
        collections = self.client.get_collections()

        return [c for c in collections]

    def search(self, query, *args, **kwargs) -> SceneResults:
        collections = query
        if type(query) not in (list, tuple,):
            collections = [query]

        data = {}
        if kwargs.get("bbox"):
            data["bbox"] = kwargs["bbox"]
        if kwargs.get("start_date"):
            data["datetime"] = kwargs["start_date"]

        item_search = self.client.search(collections=collections, **data)

        return [
            SceneResult(item.id,
                        item.properties.get("eo:cloud_cover"),
                        link=item.assets.get("PRODUCT").href,
                        **item.to_dict())
            for item in item_search.items()
        ]
