#
# This file is part of BDC-Collectors.
# Copyright (C) 2020 INPE.
#
# BDC-Collectors is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Pytest fixtures."""

import pytest
from flask import Flask

from bdc_collectors import create_app


@pytest.fixture(scope='class')
def flask():
    """Fixture to create Flask App."""
    _app = Flask('test')

    yield _app


@pytest.fixture(scope='class')
def app():
    """Fixture to create Flask app and configure BDC-Collectors Extension."""
    _app = create_app()

    with _app.app_context():
        yield _app
