..
    This file is part of BDC-Collectors.
    Copyright (C) 2023 INPE.

    BDC-Collectors is a free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.


=======
Changes
=======

Version 1.0.0 (2024-08-14)
--------------------------

- Add driver for Copernicus DataSpace EcoSystem.
- Review module dependencies
- Improve stability of driver Copernicus DataSpace EcoSystem
- Improve driver to search in provider NASA Modis
- Improve docs for command line and downloading.
- Fix MODIS api search using geometry
- Fix search in Landsat API using day/night indicator


Version 1.0.0.dev3 (2024-03-04)
-------------------------------

- Fix MODIS api search using geometry


Version 1.0.0.dev2 (2024-01-04)
-------------------------------

- Fix search in Landsat API using day/night indicator
- Improve stability of driver Copernicus DataSpace EcoSystem
- Improve driver to search in provider NASA Modis


Version 1.0.0.dev1 (2023-10-03)
-------------------------------

- Review module dependencies
- Add driver for Copernicus DataSpace EcoSystem.
- Improve docs for command line and downloading.


Version 0.9.0 (2023-01-26)
--------------------------

- Review dependencies for collections
- Minor bugs related API provider for Landsat
- Minimal support for Sentinel-1


Version 0.8.0 (2022-09-21)
--------------------------

- Change LICENSE to GPL v3 and headers source code
- Improve docs usage/setup
- Fix readthedocs build
- Remove ``bdc-catalog`` dependency
- Remove legacy providers: ``STAC`` and ``EarthSearch``.
- Set deprecation warning for methods: ``compressed_files``.


Version 0.6.1 (2022-04-04)
--------------------------

- Fix Landsat Download data from EarthExplorer (USGS) `59 <https://github.com/brazil-data-cube/bdc-collectors/issues/59>`_.


Version 0.6.0 (2022-03-25)
--------------------------

- Remove dependency bdc-catalog and move as `extras` `57 <https://github.com/brazil-data-cube/bdc-collectors/issues/57>`_.
- Add support to download Landsat-9 scenes `55 <https://github.com/brazil-data-cube/bdc-collectors/issues/55>`_.
- Improve way to deal with parallel download in Sentinel-2 `53 <https://github.com/brazil-data-cube/bdc-collectors/issues/53>`_.
- Improve error handling for MODIS download `52 <https://github.com/brazil-data-cube/bdc-collectors/issues/52>`_.
- Fix path for Landsat-8 SR collections `50 <https://github.com/brazil-data-cube/bdc-collectors/issues/50>`_.
- Review path for Sentinel-2 SR collections `46 <https://github.com/brazil-data-cube/bdc-collectors/issues/46>`_.


Version 0.4.1 (2021-07-20)
--------------------------

- Fix bug related to customize API URL for Sentinel-2 `33 <https://github.com/brazil-data-cube/bdc-collectors/issues/33>`_.


Version 0.4.0 (2021-05-04)
--------------------------

- Add support to search and download MODIS products (`#28 <https://github.com/brazil-data-cube/bdc-collectors/issues/28>`_).
- Add option to download Day/Night data acquisition for Landsat products, Set default as Day only. (`#25 <https://github.com/brazil-data-cube/bdc-collectors/issues/25>`_).
- Add support the latest USGS API 1.5, which supports Landsat Collection 2 (`#22 <https://github.com/brazil-data-cube/bdc-collectors/issues/22>`_).
- Improve documentation for ReadTheDocs.


Version 0.2.1 (2021-01-19)
--------------------------

- Fix base url for Landsat and Sentinel-2 products `#16 <https://github.com/brazil-data-cube/bdc-collectors/issues/16>`_
- Add Drone CI support `#17 <https://github.com/brazil-data-cube/bdc-collectors/issues/17>`_.


Version 0.2.0 (2020-12-02)
--------------------------

- Add support to search and download data product from the following providers:

    - `USGS Earth Explorer <https://earthexplorer.usgs.gov/>`_ (`#3 <https://github.com/brazil-data-cube/bdc-collectors/issues/3>`_).
    - `Copernicus SciHub <http://scihub.copernicus.eu/dhus/>`_ (`#1 <https://github.com/brazil-data-cube/bdc-collectors/issues/1>`_).
    - `Google Public Data Sets <https://cloud.google.com/storage/docs/public-datasets>`_ (`#2 <https://github.com/brazil-data-cube/bdc-collectors/issues/2>`_).
    - `CREODIAS <https://finder.creodias.eu/>`_ (`#5 <https://github.com/brazil-data-cube/bdc-collectors/issues/5>`_).
    - `ONDA Catalogue <https://catalogue.onda-dias.eu/catalogue/>`_ (`#4 <https://github.com/brazil-data-cube/bdc-collectors/issues/4>`_).

- Add minimal unittests for data search and download;
- Add support of the latest USGS JSON API 1.5 (`#9 <https://github.com/brazil-data-cube/bdc-collectors/issues/9>`_).
- Documentation system based on ``Sphinx`` (`#6 <https://github.com/brazil-data-cube/bdc-collectors/issues/6>`_).
- Source code versioning based on `Semantic Versioning 2.0.0 <https://semver.org/>`_.
- License: `MIT <https://github.com/brazil-data-cube/bdc-collection-builder/blob/v0.2.0/LICENSE>`_.
