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

"""Download data from Dataspace."""

import os

from flask import Flask
from bdc_collectors import CollectorExtension

from bdc_collectors.dataspace.stac import StacStrategy


app = Flask(__name__)

ext = CollectorExtension(app)

print("Using ODATA")
odata_provider = ext.get_provider('Dataspace')(
    username=os.getenv('BDC_USER', 'user@email.com'),
    password=os.getenv('BDC_PASSWORD', 'pass'),
    progress=True
)
entries_odata = odata_provider.search("SENTINEL-2", start_date="2023-06-01", end_date="2023-06-30", bbox=(-54, -12, -52, -10), product="S2MSI2A")

# Uncomment the next lines to use STAC Strategy instead ODATA method. 
# print("Using STAC method")
# stac = StacStrategy()
# provider = ext.get_provider('Dataspace')(username=os.getenv('BDC_USER', 'user@email.com'), password=os.getenv('BDC_PASSWORD', 'pass'), strategy=stac)
# entries = provider.search("SENTINEL-2", start_date="2023-06-01", end_date="2023-06-30", bbox=(-54, -12, -52, -10), product="S2MSI2A")

for entry in entries_odata:
    odata_provider.download(entry.scene_id, output="examples")
