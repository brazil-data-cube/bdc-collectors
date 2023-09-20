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

"""Define the implementation of ODATA for provider Copernicus Dataspace Program."""

import typing as t
from copy import deepcopy

from requests import Session
from shapely.geometry import base, box, shape
from shapely.wkt import loads as wkt_loads

from ..base import BaseProvider, SceneResult, SceneResults
from ..utils import get_date_time

ODATA_URL: str = "https://catalogue.dataspace.copernicus.eu/odata"
PRODUCTS_URL = "{url}/v1/Products"
STAC_RFC_DATETIME: str = "%Y-%m-%dT%H:%M:%SZ"


class ODATAStrategy(BaseProvider):
    """Represent the implementation of Copernicus Dataspace program API using ODATA (Open Data Protocol)."""

    def __init__(self, api_url: str = ODATA_URL, **kwargs):
        """Build an instance of ODATA strategy method."""
        self.session = Session()
        self.api_url = api_url

    def search(self, query, *args, **kwargs) -> SceneResults:
        """Search for data products in Copernicus Dataspace program."""
        data = deepcopy(kwargs)

        filters = []
        if data.get("ids"):
            products = []
            for item_id in data["ids"]:
                safe_id = f"{item_id}.SAFE" if not item_id.endswith(".SAFE") else item_id
                products_found = self._retrieve_products(f"Name eq '{safe_id}'")
                products.extend(products_found)

            return products
        else:
            filters.append(f"Collection/Name eq '{query}'")

        if data.get("geom"):
            geom = _get_geom(data["geom"])
            filters.append(f"OData.CSC.Intersects(area=geography'SRID=4326;{geom.wkt}')")
        if data.get("bbox"):
            bbox = box(*data.pop("bbox"))
            filters.append(f"OData.CSC.Intersects(area=geography'SRID=4326;{bbox.wkt}')")
        if data.get("start_date"):
            filters.append(f"ContentDate/Start gt {get_date_time(data.pop('start_date')).strftime(STAC_RFC_DATETIME)}")
        if data.get("end_date"):
            filters.append(f"ContentDate/Start lt {get_date_time(data.pop('end_date')).strftime(STAC_RFC_DATETIME)}")

        if data.get("product"):
            filters.append(f"Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'productType' and att/OData.CSC.StringAttribute/Value eq '{data.pop('product')}')")

        return self._retrieve_products(*filters)

    def _retrieve_products(self, *filters, **options):
        filter_expression = " and ".join(filters)
        params = {
            "$filter": filter_expression,
            "$top": 1000
        }
        params.update(**options)

        response = self.session.get(PRODUCTS_URL.format(url=self.api_url), params=params)
        if response.status_code != 200:
            raise RuntimeError(f"Error {response.status_code}: {response.content}")

        # TODO: validate code/output
        products = response.json()["value"]

        return [
            self._serialize_product(product) for product in products
        ]

    def _serialize_product(self, product: t.Dict[str, t.Any]) -> SceneResult:
        cloud_cover = 0  # TODO: Get it from STAC??
        return SceneResult(product["Name"].replace(".SAFE", ""),
                           cloud_cover,
                           link=f"{PRODUCTS_URL.format(url=self.api_url)}({product['Id']})/$value",
                           **product)



def _get_geom(geom: t.Any) -> base.BaseGeometry:
    if isinstance(geom, str):
        return wkt_loads(geom)
    elif isinstance(geom, dict):
        return shape(geom)
    elif isinstance(geom, base.BaseGeometry):
        return geom

    raise ValueError(f"Invalid geometry")
    