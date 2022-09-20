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
