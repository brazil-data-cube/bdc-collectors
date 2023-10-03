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

"""Define the implementation of STAC for provider Copernicus Dataspace Program."""

import typing as t
from copy import deepcopy

from pystac_client import Client
from requests import Session, exceptions

from ..base import BaseProvider, SceneResult, SceneResults
from ..utils import get_date_time

DEFAULT_STAC_URL: str = "https://catalogue.dataspace.copernicus.eu/stac"
STAC_RFC_DATETIME: str = "%Y-%m-%dT%H:%M:%SZ"


class StacStrategy(BaseProvider):
    """Represent the implementation of Copernicus Dataspace program API using STAC (SpatioTemporal Asset Catalog).

    Note:
        According Copernicus Dataspace docs, this method is not fully supported by STAC clients.
        We recommend to use :class:`bdc_collectors.dataspace.odata.ODATAStrategy` instead.
        See more in `STAC Product Catalog <https://documentation.dataspace.copernicus.eu/APIs/STAC.html>`_.
    """

    def __init__(self, stac_url: str = DEFAULT_STAC_URL, **kwargs):
        """Build a instance of Stac strategy method."""
        self.client = Client.open(stac_url, **kwargs)

    def collections_supported(self):
        """Retrieve the list of supported collections by STAC."""
        collections = self.client.get_collections()

        return [c.id for c in collections]

    def search(self, query, *args, **kwargs) -> SceneResults:
        """Search for data products in Copernicus Dataspace program."""
        collections = query
        if type(query) not in (list, tuple,):
            collections = [query]

        data = deepcopy(kwargs)
        if data.get("bbox"):
            data["bbox"] = data.pop("bbox")
        if data.get("start_date"):
            data["datetime"] = f'{get_date_time(data.pop("start_date")).strftime(STAC_RFC_DATETIME)}/'
        if data.get("end_date"):
            if data.get("datetime"):
                data["datetime"] += get_date_time(data.pop("end_date")).strftime(STAC_RFC_DATETIME)
            else:
                data["datetime"] = f'/{get_date_time(data.pop("end_date")).strftime(STAC_RFC_DATETIME)}'

        product = data.pop("product", None)

        if data.get("ids"):
            session = Session()
            items = []
            for item_id in data["ids"]:
                collection = self._guess_collection(item_id)
                item = self._get_item(item_id, collection, session)
                items.append(item)
        else:
            item_search = self.client.search(collections=collections, **data)
            # TODO: Remove this change when they fully supports STAC POST method
            # See https://documentation.dataspace.copernicus.eu/APIs/STAC.html
            item_search.method = "GET"
            items = list([item.to_dict() for item in item_search.items()])

        return [self._serialize_item(item) for item in items if product is None or _match_by_product(product, item)]

    def _guess_collection(self, item_id: str) -> str:
        # TODO: Use parser list
        if item_id[:3] in ("S1A", "S1B", "S2A", "S2B", "S3A", "S3B"):
            return f"SENTINEL-{item_id[1]}"
        elif item_id[:3] in ("S5P",):
            return "SENTINEL-5P"
        raise RuntimeError(f"Could not identify collection from {item_id}")

    def _get_item(self, item_id: str, collection: str, session: Session) -> SceneResult:
        item_url = f"{DEFAULT_STAC_URL}/collections/{collection}/items/{item_id}"
        response = session.get(item_url, timeout=30)
        if response.status_code != 200:
            raise exceptions.HTTPError(response.content)

        return response.json()

    def _serialize_item(self, item: t.Dict[str, t.Any]) -> SceneResult:
        if item["assets"].get("PRODUCT") is None:
            raise ValueError(f"Invalid item {item['id']}. Missing property 'PRODUCT' in assets")

        href = item["assets"]["PRODUCT"]["href"]
        scene = SceneResult(item["id"].replace(".SAFE", ""),
                            item["properties"].get("eo:cloud_cover"),
                            link=href,
                            **item)
        return scene


def _match_by_product(product: str, item: t.Dict[str, t.Any]) -> bool:
    product_type = item["properties"].get("productType")
    return product_type and product == product_type