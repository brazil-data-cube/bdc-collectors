#
# This file is part of BDC-Collectors.
# Copyright (C) 2020 INPE.
#
# BDC-Collectors is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Define the supported Landsat-7 collections in USGS Earth Explorer catalog."""

from .base import BaseLandsat


class Landsat7(BaseLandsat):
    """Simple abstraction for Landsat-7 DN."""

    bands = [
        'B1.TIF', 'B2.TIF', 'B3.TIF', 'B4.TIF', 'B5.TIF',
        'B6_VCID_1.TIF', 'B6_VCID_2.TIF', 'B7.TIF', 'B8.TIF', 'BQA.TIF'
    ]

    assets = [
        'MTL.txt',
        'ANG.txt'
    ]


class Landsat7SR(BaseLandsat):
    """Simple abstraction for Landsat-7 Surface Reflectance."""

    bands = [
        'sr_band1.tif', 'sr_band2.tif', 'sr_band3.tif', 'sr_band4.tif', 'sr_band5.tif', 'sr_band6.tif', 'sr_band7.tif', 'sr_cloud_qa.tif'
    ]

    assets = [
        'MTL.txt',
        'ANG.txt'
    ]
