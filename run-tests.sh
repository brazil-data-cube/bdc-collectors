#!/usr/bin/env bash
#
# This file is part of BDC-Collectors.
# Copyright (C) 2019-2020 INPE.
#
# BDC-Collectors is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

pydocstyle bdc_collectors tests setup.py && \
isort bdc_collectors tests setup.py --check-only --diff --skip-glob "bdc_collectors/alembic/*" && \
check-manifest --ignore ".readthedocs.yml,.drone.yml" && \
sphinx-build -qnW --color -b doctest docs/sphinx/ docs/sphinx/_build/doctest && \
pytest