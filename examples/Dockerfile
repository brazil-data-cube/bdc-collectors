#
# This file is part of BDC-Collectors.
# Copyright (C) 2020 INPE.
#
# BDC-Collectors is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

FROM python:3.8.6

ENV START_DATE ''
ENV END_DATE ''
ENV DELTA_DAYS ''
ENV DATA_DIR ''
ENV SHP_DATA_DIR ''
ENV S2_GRID_NAME ''
ENV BDC_CREODIAS_USER ''
ENV BDC_CREODIAS_PASSWORD ''

COPY . /app

WORKDIR /app

RUN pip3 install -U pip && \
    pip3 install -U setuptools && \
    pip3 install wheel && \
    pip3 install -e .[all] && \
    pip3 install fiona

CMD ["python3", "examples/download_sentinel_tile.py"]