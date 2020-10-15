#
# This file is part of BDC-Collectors.
# Copyright (C) 2020 INPE.
#
# BDC-Collectors is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Command line for BDC-Collectors."""

import logging

import click
from bdc_catalog.models import Collection
from flask import current_app
from flask.cli import FlaskGroup, with_appcontext

from . import create_app


@click.group(cls=FlaskGroup, create_app=create_app)
def cli():
    """Command line for BDC-Collectors."""


@cli.command()
@click.option('-p', '--provider', help='Provider name. (USGS, SciHub...)', required=True)
@click.option('-d', '--dataset', help='Dataset name', required=True)
@click.option('-b', '--bbox', help='Bounding Box (west, south, east, north)', required=True)
@click.option('-t', '--time', help='Time start/end', required=True)
@click.option('-u', '--username', help='User', required=False)
@click.option('--password', help='Password (if needed)', required=False)
@click.option('--platform', help='Platform sensor (if required)', required=False)
@with_appcontext
def search(provider, dataset, bbox, time, username=None, password=None, **kwargs):
    """Search for data set in the given provider.

    Args:
        provider - Provider name to search.
        dataset - Data set name in provider.
        bbox - Bounding box definition (west, south, east, north).
        time - Time interval. (start/end). Format should be (YYYY-mm-dd)
        username - Optional username used to search in provider.
        password - Optional password used to search in provider.
    """
    # Get BDC-Collectors extension and then seek for provider support.
    ext = current_app.extensions['bdc:collector']

    provider_class = ext.get_provider(provider)

    if provider_class is None:
        raise RuntimeError(f'Provider {provider} not supported.')

    # Create an instance of supported provider. We pass progress=True for
    # providers which support progress bar (SciHub).
    p = provider_class(username=username, password=password, progress=True)

    bbox = [float(elm) for elm in bbox.split(',')]

    times = time.split('/')

    start_date, end_date = times

    res = p.search(query=dataset, bbox=bbox, start_date=start_date, end_date=end_date, **kwargs)

    print(res)


@cli.command()
@click.option('-p', '--provider', required=True)
@click.option('-s', '--scene-id', help='Scene Identifier', required=True)
@click.option('-o', '--output', help='Save output directory', required=True)
@click.option('-d', '--dataset', help='Data set', required=False)
@click.option('-u', '--username', help='User', required=False)
@click.option('-P', '--password', help='Password (if needed)', required=False)
@with_appcontext
def download(provider, scene_id, output, **kwargs):
    """Search for data set in the given provider.

    Args:
        provider - Provider name to search.
        scene_id - Scene Id to download.
        output - Directory to save
        username - Optional username used to download from provider.
        password - Optional password used to download from provider.
    """
    ext = current_app.extensions['bdc:collector']

    provider_class = ext.get_provider(provider)

    kwargs.setdefault('progress', True)

    p = provider_class(**kwargs)

    result = p.download(scene_id, output=output, force=False, **kwargs)

    click.secho(f'File saved in {result}')


@cli.command()
@with_appcontext
def show_providers():
    """List the supported providers of BDC-Collectors."""
    ext = current_app.extensions['bdc:collector']

    click.secho('Supported providers: ', bold=True, fg='green')
    for provider_name in ext.list_providers():
        click.secho(f'\t{provider_name}', bold=True, fg='green')


@cli.command()
@click.option('-c', '--collection-id', required=True)
@click.option('-s', '--scene-id', required=True)
@click.option('-o', '--output', help='Save output directory', required=True)
@with_appcontext
def priority(collection_id, scene_id, output):
    """Download a scene seeking in CollectionProviders.

    Notes:
        You must configure the BDC-Catalog.

    Args:
        collection_id - Collection Identifier
        scene_id - A scene identifier (Landsat Scene Id/Sentinel Scene Id, etc)
        output - Directory to save.
    """
    ext = current_app.extensions['bdc:collector']

    collection = Collection.query().get(collection_id)

    order = ext.get_provider_order(collection)

    for driver in order:
        try:
            file_destination = driver.download(scene_id, output=output)
        except Exception as e:
            logging.warning(f'Download error for provider {driver.provider_name} - {str(e)}')


def main(as_module=False):
    """Load Brazil Data Cube (bdc_collection_builder) as module."""
    import sys
    cli.main(args=sys.argv[1:], prog_name="python -m bdc_collectors" if as_module else None)
