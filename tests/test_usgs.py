import json
import re
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Type
from unittest import mock

import pytest
from pkg_resources import resource_string

from bdc_collectors.base import BaseProvider, SceneResult
from bdc_collectors.ext import CollectorExtension


def _provider(app, name='USGS') -> Type[BaseProvider]:
    ext: CollectorExtension = app.extensions['bdc:collector']

    return ext.get_provider(name)


base_url = 'https://m2m.cr.usgs.gov/api/api/json/stable/{context}'
mock_login_url = base_url.format(context='login')
mock_logout_url = base_url.format(context='logout')
mock_search_url = base_url.format(context='scene-search')
mock_filters_url = base_url.format(context='dataset-filters')
mock_download_url = 'https://earthexplorer.usgs.gov/download/5e83d0b84df8d8c2/LC82250692020002LGN00/EE/'
# TODO: Change login version on EE to latest (1.5???)
mock_ee_login_url = 'https://ers.cr.usgs.gov/login/'
mock_ee_logout_url = 'https://earthexplorer.usgs.gov/logout'


@pytest.fixture(scope='session')
def catalog_usgs():
    search_l8 = resource_string(__name__, 'jsons/usgs-landsat-8.json')

    return json.loads(search_l8)


default_filters = json.loads(resource_string(__name__, 'jsons/filters.json'))


class TestUSGS:
    def _setup_login_logout(self, mock):
        login_html = '''
            <input name="__ncforminfo" value="AnyValue">
            <input name="csrf" value="AnyValue">
        '''

        mock.get(re.compile(mock_ee_login_url), text=login_html, status_code=200)
        mock.post(re.compile(mock_ee_login_url), text=login_html, status_code=200)
        mock.get(mock_ee_logout_url, status_code=200)

        mock.post(mock_filters_url, json={'error': [], 'data': default_filters},
                  status_code=200, headers={'content-type': 'application/json'})

    def test_missing_credentials(self, app):
        provider_class = _provider(app, 'USGS')

        assert provider_class is not None

        with pytest.raises(RuntimeError):
            provider_class()

    def test_lazy_usgs_connection(self, app, requests_mock):
        provider_class = _provider(app, 'USGS')

        requests_mock.post(mock_login_url, json={'error': [], 'data': {}}, status_code=200, headers={'content-type':'application/json'})

        provider = provider_class(username='theuser', password='thepassword', lazy=True)

        assert hasattr(provider, 'api') and provider.api is None

    def test_logout(self, app, requests_mock):
        provider_class = _provider(app, 'USGS')

        requests_mock.post(mock_login_url, json={'error': [], 'data': {}}, status_code=200,
                           headers={'content-type': 'application/json'})

        self._setup_login_logout(requests_mock)

        provider = provider_class(username='theuser', password='thepassword')

        requests_mock.post(mock_logout_url, json={'error': [], 'data': {}}, status_code=200,
                           headers={'content-type': 'application/json'})

        provider.disconnect()
        # TODO: Add another assert to match url/parameter/header with access_token
        assert requests_mock.called

    def test_provider_search(self, app, requests_mock, catalog_usgs):
        provider_class = _provider(app, 'USGS')

        assert provider_class is not None

        requests_mock.post(mock_login_url, json={'error': [], 'data': ''}, status_code=200, headers={'content-type':'application/json'})

        self._setup_login_logout(requests_mock)

        provider = provider_class(username='theuser', password='thepassword')

        assert requests_mock.called

        bbox = [-54, -12, -50, -10]

        requests_mock.post(mock_search_url, json={'error': [], 'data': dict(results=catalog_usgs)}, status_code=200, headers={'content-type':'application/json'})

        res = provider.search('LANDSAT_8_C1', start_date='2020-01-01', end_date='2020-01-31', bbox=bbox)

        for found in res:
            assert isinstance(found, SceneResult)

        # Mock logout url since it is attached to destructor
        requests_mock.post(mock_logout_url, json={'error': [], 'data': {}}, status_code=200, headers={'content-type':'application/json'})

    def test_search_and_custom_validate(self, app, requests_mock, catalog_usgs):
        provider_class = _provider(app, 'USGS')

        requests_mock.post(mock_login_url, json={'error': [], 'data': ''}, status_code=200, headers={'content-type':'application/json'})

        self._setup_login_logout(requests_mock)

        provider = provider_class(username='theuser', password='thepassword', lazy=True)

        bbox = [-54, -12, -50, -10]

        requests_mock.post(mock_search_url, json={'error': [], 'data': dict(results=catalog_usgs)}, status_code=200, headers={'content-type':'application/json'})

        def _custom_validate(scene: dict, **kwargs) -> bool:
            return scene['displayId'].endswith('T1')  # Only T1 files

        res = provider.search('LANDSAT_8_C1', start_date='2020-01-01',
                              end_date='2020-01-31', bbox=bbox, validate=_custom_validate)

        assert len(res) == 0

        invalid_validate = 'invalid_validate'

        with pytest.raises(ValueError):
            provider.search('LANDSAT_8_C1', start_date='2020-01-01',
                            end_date='2020-01-31', bbox=bbox, validate=invalid_validate)

        # Mock logout url since it is attached to destructor
        requests_mock.post(mock_logout_url, json={'error': [], 'data': {}}, status_code=200, headers={'content-type':'application/json'})

    def test_search_by_additional_criteria(self, app, requests_mock, catalog_usgs):
        provider_class = _provider(app, 'USGS')

        requests_mock.post(mock_login_url, json={'error': [], 'data': ''}, status_code=200, headers={'content-type':'application/json'})

        self._setup_login_logout(requests_mock)

        provider = provider_class(username='theuser', password='thepassword', lazy=True)

        requests_mock.post(mock_search_url, json={'error': [], 'data': dict(results=catalog_usgs)}, status_code=200, headers={'content-type':'application/json'})

        res = provider.search('LANDSAT_8_C1', tile='225067')

        assert len(res) > 0

        res = provider.search('LANDSAT_8_C1', scene_id='LC08_L1GT_225067_20200102_20200113_01_T2')

        assert len(res) > 0

        # Mock logout url since it is attached to destructor
        requests_mock.post(mock_logout_url, json={'error': [], 'data': {}}, status_code=200, headers={'content-type':'application/json'})

    def test_download(self, app, requests_mock, catalog_usgs):
        provider_class = _provider(app, 'USGS')

        requests_mock.post(mock_login_url, json={'error': [], 'data': ''}, status_code=200,
                           headers={'content-type': 'application/json'})

        self._setup_login_logout(requests_mock)

        provider = provider_class(username='theuser', password='thepassword')

        requests_mock.post(mock_search_url, json={'error': [], 'data': dict(results=catalog_usgs)}, status_code=200,
                           headers={'content-type': 'application/json'})

        dataset = 'LANDSAT_8_C1'

        requests_mock.post(base_url.format(context='scene-list-add'),
                           json={"error": None, "data": dict()},
                           status_code=200,
                           headers={'content-type': 'application/json'})

        entity = catalog_usgs[0]["entityId"]
        requests_mock.post(base_url.format(context='scene-list-get'),
                           json={"error": None, "data": [dict(entityId=entity)]},
                           status_code=200,
                           headers={'content-type': 'application/json'})

        landsat_8 = '5e83d0b84df8d8c2'
        requests_mock.post(base_url.format(context='dataset'),
                           json={"error": None, "data": dict(datasetId=landsat_8)},  # Landsat-8
                           status_code=200,
                           headers={'content-type': 'application/json'})

        requests_mock.get(f'https://earthexplorer.usgs.gov/scene/downloadoptions/{landsat_8}/{entity}',
                           text=f'<button data-productid="{landsat_8}"></button>',
                           status_code=200)

        download_url = f'https://earthexplorer.usgs.gov/download/{landsat_8}/{entity}/EE'
        scene_id = catalog_usgs[0]["displayId"]
        requests_mock.get(download_url, content=b'', status_code=200,
                           headers={
                               'content-type': 'application/gzip',
                               'Content-Length': '0',
                               'Content-Disposition': f'{scene_id}.tar.gz'
                           })

        with TemporaryDirectory() as tmp:
            destination = provider.download(scene_id, output=tmp, dataset=dataset)

            path = Path(destination)
            assert path.name == f'{scene_id}.tar.gz'
            assert path.exists() and path.stat().st_size == 0

        # Mock logout url since it is attached to destructor
        requests_mock.post(mock_logout_url, json={'error': [], 'data': {}}, status_code=200,
                           headers={'content-type': 'application/json'})
