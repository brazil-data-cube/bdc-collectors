#
# This file is part of BDC-Collectors.
# Copyright (C) 2020 INPE.
#
# BDC-Collectors is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Define the module for dealing with NASA MODIS products."""

from .api import ModisAPI
from .parser import ModisScene


def init_provider():
    """Register the NASA Modis provider."""
    return dict(
        MODIS=ModisAPI
    )


__all__ = (
    'init_provider',
    'ModisAPI',
    'ModisScene',
)
