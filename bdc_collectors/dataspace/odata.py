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

import logging
import typing as t
from copy import deepcopy

from requests import PreparedRequest, Session
from shapely.geometry import box

from ..base import BaseProvider, SceneResult, SceneResults
from ..utils import get_date_time, to_geom

ODATA_URL: str = "https://catalogue.dataspace.copernicus.eu/odata"
PRODUCTS_URL = "{url}/v1/Products"
STAC_RFC_DATETIME: str = "%Y-%m-%dT%H:%M:%SZ"


class ODATAStrategy(BaseProvider):
    """Represent the implementation of Copernicus Dataspace program API using ODATA (Open Data Protocol)."""

    def __init__(self,
                 odata_api_url: str = ODATA_URL,
                 odata_api_max_records: int = 12000,
                 odata_api_limit: int = 500,
                 **kwargs):
        """Build an instance of ODATA strategy method."""
        self.session = Session()
        self.api_url = odata_api_url
        self._odata_api_max_records = odata_api_max_records
        self._odata_api_limit = odata_api_limit

    def search(self, query, *args, **kwargs) -> SceneResults:
        """Search for data products in Copernicus Dataspace program."""
        data = deepcopy(kwargs)

        filters = []
        if data.get("ids"):
            products = []
            for item_id in data["ids"]:
                products_found = self._retrieve_products(f"Name eq '{item_id}'")
                products.extend(products_found)

            return products
        else:
            filters.append(f"Collection/Name eq '{query}'")

        if data.get("geom"):
            geom = to_geom(data["geom"])
            filters.append(f"OData.CSC.Intersects(area=geography'SRID=4326;{geom.wkt}')")
        if data.get("bbox"):
            bbox = box(*data.pop("bbox"))
            filters.append(f"OData.CSC.Intersects(area=geography'SRID=4326;{bbox.wkt}')")
        if data.get("start_date"):
            filters.append(f"ContentDate/Start gt {get_date_time(data.pop('start_date')).strftime(STAC_RFC_DATETIME)}")
        if data.get("end_date"):
            filters.append(f"ContentDate/Start lt {get_date_time(data.pop('end_date')).strftime(STAC_RFC_DATETIME)}")

        # Specific attribute helpers
        # TODO: Implement an adaptative method to deal these attribute names which supports comparators like eq/lt/gt etc
        for entry in ["productType", "instrumentShortName"]:
            if data.get(entry):
                filters.append(f"Attributes/OData.CSC.StringAttribute/any(att:att/Name eq '{entry}' and att/OData.CSC.StringAttribute/Value eq '{data.pop(entry)}')")

        # For unmapped attribute filter, the user may specify manual attributes
        # attributes = ["Attributes/....... eq '10'"]
        if data.get("attributes"):
            if not isinstance(data["attributes"], t.Iterable):
                raise TypeError("Invalid value for 'attributes'.")

            filters.extend(data["attributes"])

        return self._retrieve_products(*filters)

    def _retrieve_products(self, *filters, **options):
        filter_expression = " and ".join(filters)
        params = {
            "$filter": filter_expression,
            "$top": self._odata_api_limit,
            "$expand": "Attributes",
            "$orderby": "ContentDate/Start desc"
        }
        params.update(**options)

        products: t.List[t.Dict[str, t.Any]] = []

        prepared = PreparedRequest()
        prepared.prepare_url(PRODUCTS_URL.format(url=self.api_url), params)
        url = prepared.url

        while True:
            response = self.session.get(url)
            if response.status_code != 200:
                raise RuntimeError(f"Error {response.status_code}: {response.content}")

            data = response.json()
            products_found = data["value"]
            if len(products_found) == 0:
                break

            products.extend(products_found)

            if data.get("@odata.nextLink") is None:
                break

            url = data.get("@odata.nextLink")

            # Break control for too many records 
            if len(products) > self._odata_api_max_records:
                logging.warning(f"Max records for BDC Collectors DataSpace ODATA API reached limit {self._odata_api_max_records}. Skipping.")
                break

        return [
            self._serialize_product(product) for product in products
        ]

    def _serialize_product(self, product: t.Dict[str, t.Any]) -> SceneResult:
        attribute_dict = {
            attribute["Name"]: attribute["Value"] for attribute in product["Attributes"]
        }
        product.pop("Attributes")
        return SceneResult(product["Name"].replace(".SAFE", "").replace(".SEN3", ""),
                           attribute_dict.get("cloudCover"),
                           link=f"{PRODUCTS_URL.format(url=self.api_url)}({product['Id']})/$value",
                           **product,
                           **attribute_dict)
