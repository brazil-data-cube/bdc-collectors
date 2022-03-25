#
# This file is part of BDC-Collectors.
# Copyright (C) 2020 INPE.
#
# BDC-Collectors is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Setup for BDC-Collectors."""

import os

from setuptools import find_packages, setup

readme = open('README.rst').read()

history = open('CHANGES.rst').read()

docs_require = [
    'Sphinx>=2.2',
    'sphinx_rtd_theme',
    'sphinx-copybutton',
    'sphinx-tabs',
]

tests_require = [
    'coverage>=4.5',
    'pytest>=5.2',
    'pytest-cov>=2.8',
    'pytest-pep8>=1.0',
    'pydocstyle>=4.0',
    'isort>4.3',
    'check-manifest>=0.40',
    'requests-mock>=1.7'
]

extras_require = {
    'docs': docs_require,
    'tests': tests_require,
    'modis': [
        'pymodis>=2.1,<2.2'
    ],
    'catalog': [
        'bdc-catalog @ git+https://github.com/brazil-data-cube/bdc-catalog@v0.8.2',
    ]
}

extras_require['all'] = [req for _, reqs in extras_require.items() for req in reqs]

setup_requires = [
    'pytest-runner>=5.2',
]

install_requires = [
    'python-dateutil>=2',
    'Flask>=1.1.0',
    'google-cloud-storage>=1.28,<2',
    'beautifulsoup4>=4.9,<5',
    'rasterio>=1.1,<1.3',
    'redis>=3.5,<4',
    'sentinelsat>=0.14,<1',
    'Shapely>=1.7,<2',
    'stac.py>=0.9',
    'tqdm>=4.50'
]

packages = find_packages()

g = {}
with open(os.path.join('bdc_collectors', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

setup(
    name='bdc-collectors',
    version=version,
    description=__doc__,
    long_description=readme + '\n\n' + history,
    keywords=['database', 'postgresql'],
    license='MIT',
    author='Brazil Data Cube Team',
    author_email='brazildatacube@inpe.br',
    url='https://github.com/brazil-data-cube/bdc-collectors',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'console_scripts': [
            'bdc-collector = bdc_collectors.cli:cli'
        ],
        'bdc_collectors.providers': [
            'creodias = bdc_collectors.creodias',
            'earth_search = bdc_collectors.earth_search',
            'google = bdc_collectors.google',
            'usgs = bdc_collectors.usgs',
            'onda = bdc_collectors.onda',
            'scihub = bdc_collectors.scihub',
            'dgi = bdc_collectors.dgi',
            'modis = bdc_collectors.modis',
        ],
        'bdc_db.scripts': [
            'bdc_collectors = bdc_collectors.scripts'
        ]
    },
    extras_require=extras_require,
    install_requires=install_requires,
    setup_requires=setup_requires,
    tests_require=tests_require,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Scientific/Engineering :: GIS',
    ],
)
