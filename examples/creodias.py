#
# This file is part of BDC-Collectors.
# Copyright (C) 2020 INPE.
#
# BDC-Collectors is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Download data from CREODIAS."""

import os

from flask import Flask
from bdc_collectors import CollectorExtension


app = Flask(__name__)

ext = CollectorExtension(app)

provider = ext.get_provider('CREODIAS')(username=os.getenv('BDC_USER', 'user@email.com'), password=os.getenv('BDC_PASSWORD', 'pass'))

SCENES = [
    "S2B_MSIL1C_20170919T140039_N0205_R067_T22MCB_20170919T140040",
    "S2B_MSIL1C_20170906T135109_N0205_R024_T22MCB_20170906T135105",
    "S2B_MSIL1C_20170926T135059_N0205_R024_T22MDB_20170926T135300",
    "S2B_MSIL1C_20170909T140259_N0205_R067_T22MBB_20170909T140259",
    "S2B_MSIL1C_20170919T140039_N0205_R067_T22MBB_20170919T140040",
    "S2A_MSIL1C_20170911T135111_N0205_R024_T22MCB_20170911T135110",
    "S2A_MSIL1C_20170904T140051_N0205_R067_T22MBB_20170904T140051",
    "S2B_MSIL1C_20170909T140259_N0205_R067_T22MCB_20170909T140259",
    "S2B_MSIL1C_20170926T135059_N0205_R024_T22MCB_20170926T135300",
    "S2A_MSIL1C_20170924T140051_N0205_R067_T22MCB_20170924T140106",
    "S2B_MSIL1C_20170906T135109_N0205_R024_T22MDB_20170906T135105",
]

for scene in SCENES:
    res = provider.download(scene, output=os.getenv('DATA_DIR', '/tmp'))
