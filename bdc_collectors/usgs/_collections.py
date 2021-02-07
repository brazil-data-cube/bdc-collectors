#
# This file is part of BDC-Collectors.
# Copyright (C) 2020 INPE.
#
# BDC-Collectors is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Represent a collection resolvers for USGS provider."""
from typing import Callable

import bs4


def default_download_resolver(soup: bs4.BeautifulSoup, reverse=True):
    """Define the default resolver download link for USGS API."""
    product_id = None

    # Sort buttons matches
    buttons = soup.findAll('button')
    if reverse:
        buttons = buttons[::-1]

    for button in buttons:
        if button.has_attr('data-productid'):
            product_id = button['data-productid']
            break

    return product_id


def download_resolver_landsat_c1(soup: bs4.BeautifulSoup):
    """Define a link resolver for Landsat Collection 1.

    The download options page for Collection 1 refers the link in bottom of HTML links.
    """
    return default_download_resolver(soup)


def download_resolver_landsat_c2(soup: bs4.BeautifulSoup):
    """Define a link resolver for Landsat Collection 1.

    The download options page for Collection 1 refers the link on top of HTML link.
    """
    return default_download_resolver(soup, reverse=False)


def get_resolver(data_set_name: str) -> Callable[[bs4.BeautifulSoup], str]:
    """Get a common download link resolver based in data set name."""
    name = data_set_name.lower()
    if name.startswith('landsat'):
        if '_c1' in name:
            return download_resolver_landsat_c1
        return download_resolver_landsat_c2
    raise RuntimeError(f'Data set name "{data_set_name}" not supported in bdc-collectors.')
