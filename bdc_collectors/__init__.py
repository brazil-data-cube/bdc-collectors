#
# This file is part of BDC-Collectors.
# Copyright (C) 2020 INPE.
#
# BDC-Collectors is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Python module for Brazil Data Cube Collectors."""

from flask import Flask

from .ext import CollectorExtension
from .version import __version__


def create_app() -> Flask:
    """Create instance of Flask application for BDC-Collectors."""
    from bdc_catalog.ext import BDCCatalog

    app = Flask(__name__)

    # TODO: We should remove the BDC-Catalog initialization and pass to the invoker.
    BDCCatalog(app)
    CollectorExtension(app)

    return app


__all__ = (
    '__version__',
    'create_app',
    'CollectorExtension',
)
