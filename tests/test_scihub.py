import json
import re
from typing import Type

import pytest
from pkg_resources import resource_string

from bdc_collectors.base import BaseProvider, SceneResult
from bdc_collectors.ext import CollectorExtension


def _provider(app, name='SciHub') -> Type[BaseProvider]:
    ext: CollectorExtension = app.extensions['bdc_collector']

    return ext.get_provider(name)


base_url = 'https://apihub.copernicus.eu/apihub/'
search_url = base_url + 'search'


@pytest.fixture
def requests_mock(requests_mock):
    requests_mock.get(re.compile(base_url))
    yield requests_mock


@pytest.fixture(scope='session')
def catalog_scihub():
    search_s2 = resource_string(__name__, 'jsons/scihub-sentinel-2.json')

    return json.loads(search_s2)


class TestSciHub:
    def test_missing_credentials(self, app):
        provider_class = _provider(app)

        assert provider_class is not None

        with pytest.raises(RuntimeError):
            provider_class()

    def test_lazy_scihub_connection(self, app, requests_mock):
        provider_class = _provider(app)

        requests_mock.post(base_url, json={'error': [], 'data': {}}, status_code=200, headers={'content-type':'application/json'})

        provider = provider_class(username='theuser', password='thepassword', lazy=True)

        assert hasattr(provider, 'api')

    def test_search(self, app, requests_mock, catalog_scihub):
        provider_class = _provider(app)

        requests_mock.post(base_url, json={'error': [], 'data': {}}, status_code=200,
                           headers={'content-type': 'application/json'})

        provider = provider_class(username='theuser', password='thepassword', lazy=True)

        json_result = dict(
            feed={
                "opensearch:totalResults": len(catalog_scihub),
                "entry": catalog_scihub
            }
        )

        requests_mock.post(search_url, json=json_result, status_code=200, headers={'content-type': 'application/json'})

        res = provider.search('S2MSI1C', start_date='2020-01-01', end_date='2020-01-10',
                              platform='Sentinel-2', cloud_cover=100, bbox=[-54, -12, -52, -10])

        assert len(res) > 0

        for scene in res:
            assert isinstance(scene, SceneResult)

    # TODO: Implement test download
    # def test_download(self):
    #     pass