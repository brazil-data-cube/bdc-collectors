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
    'raster': [
        'rasterio>=1.1'
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
    'redis>=3.5,<4',
    'sentinelsat>=0.14,<1.2',
    'Shapely>=1.7,<2',
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
    license='GPLv3',
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
        'License :: OSI Approved :: GPL v3 License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Scientific/Engineering :: GIS',
    ],
)
