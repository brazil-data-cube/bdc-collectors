..
    This file is part of BDC-Collectors.
    Copyright (C) 2019-2020 INPE.

    BDC-Collectors is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.


Installation
============


Development installation
------------------------


Pre-Requirements
++++++++++++++++


The ``Brazil Data Cube Collectors`` (``BDC-Collectors``) depends essentially on:

- `Python Client Library for STAC (stac.py) <https://github.com/brazil-data-cube/stac.py>`_

- `Flask <https://palletsprojects.com/p/flask/>`_

- `BDC-Catalog <https://bdc-catalog.readthedocs.io/en/latest/>`_.

- `rasterio <https://rasterio.readthedocs.io/en/latest/>`_

- `Shapely <https://shapely.readthedocs.io/en/latest/manual.html>`_


Clone the software repository
+++++++++++++++++++++++++++++


Use ``git`` to clone the software repository::

    git clone https://github.com/brazil-data-cube/bdc-collectors.git


Install BDC-Collectors in Development Mode
++++++++++++++++++++++++++++++++++++++++++


Go to the source code folder::

    cd bdc-collectors


Install in development mode::

    pip3 install -e .[all]


.. note::

    If you want to create a new *Python Virtual Environment*, please, follow this instruction:

    *1.* Create a new virtual environment linked to Python 3.7::

        python3.7 -m venv venv


    **2.** Activate the new environment::

        source venv/bin/activate


    **3.** Update pip and setuptools::

        pip3 install --upgrade pip

        pip3 install --upgrade setuptools


Build the Documentation
+++++++++++++++++++++++


You can generate the documentation based on Sphinx with the following command::

    python setup.py build_sphinx


The above command will generate the documentation in HTML and it will place it under:

.. code-block:: shell

    doc/sphinx/_build/html/


The above command will generate the documentation in HTML and it will place it under::

    docs/sphinx/_build/html/


You can open the above documentation in your favorite browser, as::

    firefox docs/sphinx/_build/html/index.html