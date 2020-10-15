#
# This file is part of BDC-Collectors.
# Copyright (C) 2020 INPE.
#
# BDC-Collectors is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Defines the structure for Collections on remote SciHub server."""

from .base import SentinelCollection
from .parser import Sentinel1Scene


class Sentinel1(SentinelCollection):
    """Simple abstraction for Sentinel-1."""

    parser_class = Sentinel1Scene


class Sentinel2(SentinelCollection):
    """Simple abstraction for Sentinel-2."""
