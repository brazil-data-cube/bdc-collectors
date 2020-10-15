import os
import re
from tempfile import TemporaryDirectory

import pytest
import requests

from bdc_collectors.exceptions import DownloadError
from bdc_collectors.utils import download_stream, working_directory


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
