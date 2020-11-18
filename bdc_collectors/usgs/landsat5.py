#
# This file is part of BDC-Collectors.
# Copyright (C) 2020 INPE.
#
# BDC-Collectors is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Define the supported Landsat-5 collections in USGS Earth Explorer catalog."""

from .base import BaseLandsat


class Landsat5(BaseLandsat):
    """Simple abstraction for Landsat-5 DN."""

    bands = [
        'B1.TIF', 'B2.TIF', 'B3.TIF', 'B4.TIF', 'B5.TIF', 'B6.TIF', 'B7.TIF', 'BQA.TIF'
    ]


class Landsat5SR(BaseLandsat):
    """Simple abstraction for Landsat-5 Surface Reflectance."""

    bands = [
        'sr_band1.tif', 'sr_band2.tif', 'sr_band3.tif', 'sr_band4.tif', 'sr_band5.tif', 'sr_band6.tif', 'sr_band7.tif', 'sr_cloud_qa.tif'
    ]
