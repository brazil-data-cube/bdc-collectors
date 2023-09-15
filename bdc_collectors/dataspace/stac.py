from copy import deepcopy
import typing as t

from pystac_client import Client

from ..base import BaseProvider, SceneResults, SceneResult
from ..scihub.sentinel2 import Sentinel2
from ..utils import get_date_time


DEFAULT_STAC_URL: str = "https://catalogue.dataspace.copernicus.eu/stac"
STAC_RFC_DATETIME: str = "%Y-%m-%dT%H:%M:%SZ"


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

        data = deepcopy(kwargs)
        if data.get("bbox"):
            data["bbox"] = data.pop("bbox")
        if data.get("start_date"):
            data["datetime"] = f'{get_date_time(data.pop("start_date")).strftime(STAC_RFC_DATETIME)}/'
        if data.get("end_date"):
            if data.get("start_date"):
                data["datetime"] += get_date_time(data.pop("end_date")).strftime(STAC_RFC_DATETIME)
            else:
                data["datetime"] = f'/{get_date_time(data.pop("end_date")).strftime(STAC_RFC_DATETIME)}'

        item_search = self.client.search(collections=collections, **data)
        # TODO: Remove this change when they fully supports STAC POST method
        # See https://documentation.dataspace.copernicus.eu/APIs/STAC.html
        item_search.method = "GET"

        return [
            SceneResult(item.id.replace(".SAFE", ""),
                        item.properties.get("eo:cloud_cover"),
                        link=item.assets.get("PRODUCT").href,
                        **item.to_dict())
            for item in item_search.items()
        ]
