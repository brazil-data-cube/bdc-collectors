#
# This file is part of BDC-Collectors.
# Copyright (C) 2020 INPE.
#
# BDC-Collectors is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Define the supported Landsat-8 collections in USGS Earth Explorer catalog."""

from .base import BaseLandsat


class Landsat8(BaseLandsat):
    """Simple abstraction for Landsat-8."""

    bands = [
        'B1.TIF', 'B2.TIF', 'B3.TIF', 'B4.TIF', 'B5.TIF',
        'B6.TIF', 'B7.TIF', 'B8.TIF', 'B9.TIF', 'B10.TIF',
        'B11.TIF', 'BQA.TIF',
        # Collection 2
        'QA_PIXEL.TIF', 'QA_RADSAT.TIF', 'SR_QA_AEROSOL.TIF'
        'VAA.TIF', 'VZA.TIF', 'SAA.TIF', 'SZA.TIF',
        'ST_ATRAN.TIF', 'ST_B10.TIF', 'ST_CDIST.TIF', 'ST_DRAD.TIF',
        'ST_EMIS.TIF', 'ST_EMSD.TIF', 'ST_QA.TIF', 'ST_TRAD.TIF', 'ST_URAD.TIF'
    ]
