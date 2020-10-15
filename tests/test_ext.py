import json
import re
from typing import Type
from unittest import mock

import pytest
from pkg_resources import EntryPoint, resource_string
from werkzeug.utils import import_string

from bdc_collectors.base import BaseProvider, SceneResult
from bdc_collectors.ext import CollectorExtension


def _provider(app, name='USGS') -> Type[BaseProvider]:
    ext = _extension(app)

    return ext.get_provider(name)


def _extension(app) -> CollectorExtension:
    return app.extensions['bdc:collector']


class MockEntryPoint(EntryPoint):
    def load(self):
        if self.name == 'importfail':
            raise ImportError()
        else:
            return import_string(self.name)


def _mock_entry_points(name):
    data = {
        'bdc_collectors.providers': [
            MockEntryPoint('demo_provider', 'demo_provider'),
        ],
    }
    names = data.keys() if name is None else [name]
    for key in names:
        for entry_point in data.get(key, []):
            yield entry_point


class FakeProvider(BaseProvider):
    def search(self, query, *args, **kwargs):
        return [SceneResult('theid', 100)]

    def download(self, scene_id: str, *args, **kwargs) -> str:
        """Pass"""


class TestCollectorExtension:
    def test_get_provider(self, app, requests_mock):
        provider_class = _provider(app, 'USGS')

        assert provider_class is not None

    def test_add_provider(self, app):
        ext = _extension(app)

        ext.state.add_provider('FAKE', FakeProvider)

        assert 'FAKE' in ext.state.providers

        with pytest.raises(AssertionError):
            ext.state.add_provider('FAKE', FakeProvider)

    @mock.patch('pkg_resources.iter_entry_points', _mock_entry_points)
    def test_load_provider_through_entrypoint(self, flask):
        ext = CollectorExtension(flask)

        provider_class = ext.get_provider('DEMO')

        assert provider_class is not None

    def test_list_providers(self, app):
        ext = _extension(app)

        providers = ext.list_providers()

        assert len(providers) > 0