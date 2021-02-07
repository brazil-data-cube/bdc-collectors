..
    This file is part of BDC-Collectors.
    Copyright (C) 2019-2020 INPE.

    BDC-Collectors is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.


Usage
=====


Command-Line Interface (CLI)
----------------------------


The ``BDC-Collectors`` extension installs a command line tool named ``bdc-collector``:

- ``show-providers``: List all the supported providers.

- ``search``: Search for products on remote server.

- ``download``: Download scenes from remote server.

- ``priority``: Download scenes associated with ``bdc_catalog.models.Collection`` and ``bdc_catalog.models.Provider``.


Search Data sets
++++++++++++++++

The command ``search`` has the following parameters::

    Search for data set in the given provider.

    Options:
        -p --provider TEXT [required]  Provider name to search.
        -d --dataset  TEXT [required]  Data set name  in provider.
        -b --bbox     TEXT [required]  Bounding box definition (west, south, east, north).
        -t --time     TEXT [required]  Time interval. (start/end). Format should be (YYYY-mm-dd)
        -u --username TEXT             Optional username used to search in provider.
           --password TEXT             Optional password used to search in provider.
           --platform TEXT             Platform sensor (if required)
           --help                      Show this message and exit.

SciHub
~~~~~~

To search for Sentinel-2 L1 in `SciHub <https://scihub.copernicus.eu/dhus/>`_ catalog::

    bdc-collector search --provider=SciHub \
                         --dataset=S2MSI1C \
                         --platform=Sentinel-2 \
                         --time=2020-01-01/2020-01-15 \
                         --bbox=-54,-12,-50,-10 \
                         --username=user \
                         --password=password


To search for Sentinel-1 GRD in `SciHub <https://scihub.copernicus.eu/dhus/>`_ catalog::

    bdc-collector search --provider=SciHub \
                         --dataset=GRD \
                         --platform=Sentinel-1 \
                         --time=2020-01-01/2020-01-15 \
                         --bbox=-54,-12,-50,-10 \
                         --username=user \
                         --password=password

.. note::

    Make sure to change ``--username`` and ``--password``. You can create an account in
    `SciHub Registration <https://scihub.copernicus.eu/dhus/#/self-registration>`_.

    You can also search for `Sentinel-2` `L2A` products. Use ``dataset=S2MSI2A`` and ``platform=Sentinel-2``.


USGS
~~~~

To search for Landsat-8 Digital Number in `USGS Earth Explorer <https://earthexplorer.usgs.gov/>`_::

    bdc-collector search --provider=USGS \
                         --dataset=LANDSAT_8_C1 \
                         --time=2020-01-01/2020-01-15 \
                         --bbox=-54,-12,-50,-10 \
                         --username=user \
                         --password=password


.. note::

    Make sure to change ``--username`` and ``--password``. You can create an account in
    `USGS EROS Registration <https://ers.cr.usgs.gov/register>`_.

    You can also search for others Landsat products:

        - ``Landsat-4/5 Collection 1 L1``, use ``dataset=LANDSAT_TM_C1``
        - ``Landsat-7 Collection 1 L1``, use ``dataset=LANDSAT_ETM_C1``
        - ``Landsat-4/5 Collection 2 L1``, use ``dataset=landsat_tm_c2_l1``
        - ``Landsat-4/5 Collection 2 L2``, use ``dataset=landsat_tm_c2_l2``
        - ``Landsat-7 Collection 2 L1``, use ``dataset=landsat_etm_c2_l1``
        - ``Landsat-7 Collection 2 L2``, use ``dataset=landsat_etm_c2_l2``
        - ``Landsat-8 Collection 2 L1``, use ``dataset=landsat_ot_c2_l1``
        - ``Landsat-8 Collection 2 L2``, use ``dataset=landsat_ot_c2_l2``

    We still do not support others data sets like MODIS, Sentinel-2 from USGS.

Download scenes
+++++++++++++++

The command ``download`` has the following parameters::

    Search for data set in the given provider.

    Options:
        -p, --provider TEXT [required] Provider name to search
        -s, --scene-id TEXT [required] Scene Identifier to download.
        -o, --output   TEXT [required] Save output directory
        -u, --username TEXT            Optional username to download
        -P, --password TEXT            User password
            --help                     Show this message and exit.


.. note::

    Currently, you can only download by ``scene_id`` like ``S2B_MSIL1C_20200223T135109_N0209_R024_T21LZG_20200223T153255``.

    We will implement way to download from tiles, since some apis (`sentinel-sat` - `SciHub`) already support this feature.


USGS
~~~~

To download Landsat-8 Digital Number from `USGS Earth Explorer <https://earthexplorer.usgs.gov/>`_::

    bdc-collector download --provider=USGS \
                           --scene-id=LC08_L1TP_223064_20200831_20200906_01_T1 \
                           --dataset=LANDSAT_8_C1 \
                           --output=. \
                           --username=user \
                           --password=password


SciHub
~~~~~~

To download Sentinel-2 from `SciHub <https://scihub.copernicus.eu/dhus/>`_::

    bdc-collector download --provider=SciHub \
                           --scene-id=S2B_MSIL1C_20200223T135109_N0209_R024_T21LZG_20200223T153255 \
                           --output=. \
                           --username=user \
                           --password=password

To download L2A::

    bdc-collector download --provider=SciHub \
                           --scene-id=S2B_MSIL2A_20200930T135119_N0214_R024_T21KXA_20200930T175714 \
                           --output=. \
                           --username=user \
                           --password=password


Google Public Data Sets
~~~~~~~~~~~~~~~~~~~~~~~

You can also download both Landsat Digital Number and Sentinel-2 (L1C/L2A) from `Google Public Data Sets <https://cloud.google.com/storage/docs/public-datasets>`_.
In order to do that, you will need to create an `Google Service Account Key <https://console.cloud.google.com/projectselector2/iam-admin/serviceaccounts>`_ and export
the variable ``GOOGLE_APPLICATION_CREDENTIALS=path/to/google/your_service_account_key.json``.::


    export GOOGLE_APPLICATION_CREDENTIALS=path/to/google/your_service_account_key.json

    bdc-collector download --provider=Google \
                           --scene-id=LC08_L1TP_223064_20200831_20200906_01_T1 \
                           --output=.


You can download Sentinel-2 produts with::

    export GOOGLE_APPLICATION_CREDENTIALS=path/to/google/your_service_account_key.json

    bdc-collector download --provider=Google \
                           --scene-id=S2B_MSIL1C_20200223T135109_N0209_R024_T21LZG_20200223T153255 \
                           --output=.


ONDA Catalogue
~~~~~~~~~~~~~~

You can also download Sentinel scenes from alternative `ONDA DIAS Catalogue <https://catalogue.onda-dias.eu/catalogue/>`_.

In order to do that, you must have an account `ONDA User Portal Registration <https://onda-dias.eu/userportal/self-registration>`_.::

    bdc-collector download --provider=ONDA \
                           --scene-id=S2B_MSIL1C_20200223T135109_N0209_R024_T21LZG_20200223T153255 \
                           --output=. \
                           --username=user \
                           --password=password


Preparing a new package with BDC-Collectors
-------------------------------------------

In order to attach ``BDC-Collectors`` into your application, use the following statements:

.. code-block:: python

    from flask import flask
    from bdc_collectors.ext import CollectorExtension

    app = Flask(__name__)
    CollectorExtension(app)

.. note::

    If you would like to connect into database with ``BDC-Catalog``, make sure to follow the steps defined in
    `BDC-Catalog <https://bdc-catalog.readthedocs.io/en/latest/>`_.



Preparing a new provider for BDC-Collectors
-------------------------------------------


The ``BDC-Collectors`` follows the `Python Entry point specification <https://packaging.python.org/specifications/entry-points/>`_ to
discover and load libraries dynamically.


Basically, the ``BDC-Collectors`` has the following entry points to deal with dynamic data provider:

- ``bdc_db.providers``: Entry point to configure the default Catalog Providers. Append new values in your application and make sure to initialize `CollectorExtension` to make your own providers available.


.. note::

    You can also set ``bdc_db.scripts`` if you would like to insert a new SQL for data provider.
    Check `BDC-DB <https://bdc-db.readthedocs.io/en/latest/>`_ for further details.


These entry points may be defined in the ``setup.py`` of your package.


The following code is an example of an ``entry_points`` in ``setup.py`` file:


.. code-block:: python

    entry_points={
        'bdc_collectors.providers': [
            'mycatalog = my_app.mycatalog'
        ]
    }
