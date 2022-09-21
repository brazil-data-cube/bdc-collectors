#
# This file is part of Brazil Data Cube BDC-Collectors.
# Copyright (C) 2022 INPE.
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

"""Define the supported Landsat-5 collections in USGS Earth Explorer catalog."""

from .base import BaseLandsat


class Landsat5(BaseLandsat):
    """Simple abstraction for Landsat-5 DN."""

    bands = [
        'B1.TIF', 'B2.TIF', 'B3.TIF', 'B4.TIF', 'B5.TIF', 'B6.TIF', 'B7.TIF', 'BQA.TIF',
        # Collection 2
        'QA_PIXEL.TIF', 'QA_RADSAT.TIF', 'SR_ATMOS_OPACITY.TIF'
        'ST_ATRAN.TIF', 'ST_B6.TIF', 'ST_CDIST.TIF',
        'ST_DRAD.TIF', 'ST_EMIS.TIF', 'ST_EMSD.TIF', 'ST_QA.TIF', 'ST_TRAD.TIF', 'ST_URAD.TIF',
        'VAA.TIF', 'VZA.TIF', 'SAA.TIF', 'SZA.TIF',
    ]
