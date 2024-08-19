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

import os
import re
from tempfile import TemporaryDirectory

import pytest
import requests
import shapely.geometry

from bdc_collectors.exceptions import DownloadError
from bdc_collectors.utils import download_stream, to_geom, working_directory


@pytest.fixture
def requests_mock(requests_mock):
    requests_mock.get(re.compile('https://geojson.org/'))
    yield requests_mock


mock_url = 'http://localhost'


def test_download_stream(requests_mock):
    requests_mock.get(mock_url, content=b'1',
                      status_code=200,
                      headers={
                          'content-type': 'application/gzip',
                          'Content-Length': '1',
                      })

    resp = requests.get(mock_url, stream=True)

    with TemporaryDirectory() as tmp:
        out = os.path.join(tmp, 'file')

        download_stream(out, resp)

        assert os.path.exists(out) and os.stat(out).st_size == 1


def test_remove_file_corrupt_download_stream(requests_mock):
    requests_mock.get(mock_url, content=b'',
                      status_code=200,
                      headers={
                          'content-type': 'application/gzip',
                          'Content-Length': '1',
                      })

    resp = requests.get(mock_url, stream=True)

    with TemporaryDirectory() as tmp:
        out = os.path.join(tmp, 'file')

        with pytest.raises(DownloadError):
            download_stream(out, resp)

        assert not os.path.exists(out)


def test_change_work_dir():
    old = os.getcwd()

    with TemporaryDirectory() as tmp:
        with working_directory(tmp):
            assert os.getcwd() == tmp

    assert os.getcwd() == old


def test_to_geom():
    for value in ["POINT(-54 -12)", shapely.geometry.Point(-53, -15), {"type": "Point", "coordinates": [-47, -10]}]:
        geom = to_geom(value)
        assert isinstance(geom, shapely.geometry.base.BaseGeometry)

    with pytest.raises(ValueError) as exc:
        to_geom(10)

    exc.match("Invalid geometry")

    with pytest.raises(shapely.errors.GEOSException) as exc:
        to_geom("PPOINT (-54 -12)")
    exc.match("ParseException: Unknown type: 'PPOINT'")
