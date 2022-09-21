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