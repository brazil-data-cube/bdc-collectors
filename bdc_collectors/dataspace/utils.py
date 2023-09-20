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

"""Represent the code utilities for module dataspace."""

import requests

DEFAULT_TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
"""Token exchange endpoint for Copernicus Dataspace program."""


def get_access_token(username: str, password: str, client_id: str = "cdse-public",
                     token_url: str = DEFAULT_TOKEN_URL) -> str:
    """Exchange a new token for access in Copernicus Dataspace Program."""
    data = {
        "client_id": client_id,
        "username": username,
        "password": password,
        "grant_type": "password",
    }
    try:
        response = requests.post(token_url, data=data)
        response.raise_for_status()
    except requests.HTTPError as e:
        raise Exception(
            f"Access token creation failed. Response from the server was: {e.response.json()}"
        )

    if response.headers.get("content-type") != "application/json":
        raise RuntimeError(f"No valid JSON response for Access Token, got {response.content}")

    # Ensure data is JSON
    data = response.json()
    if not data.get("access_token"):
        raise RuntimeError("Server did not returned Access Token")

    return data["access_token"]
