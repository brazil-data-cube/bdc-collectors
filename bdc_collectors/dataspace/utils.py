import json

import requests


DEFAULT_TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
"""Token exchange endpoint for Copernicus Dataspace program."""


def get_access_token(username: str, password: str, client_id: str = "cdse-public",
                     token_url: str = DEFAULT_TOKEN_URL) -> str:
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
