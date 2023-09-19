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

"""Command line for BDC-Collectors."""
import json
from pathlib import Path

import click
from flask import current_app
from flask.cli import FlaskGroup, with_appcontext

from . import create_app


@click.group(cls=FlaskGroup, create_app=create_app)
def cli():
    """Command line for BDC-Collectors."""
    click.secho("""BDC-Collectors  Copyright (C) 2022  INPE
This program comes with ABSOLUTELY NO WARRANTY; for details type `show w'.
This is free software, and you are welcome to redistribute it
under certain conditions; type `show c' for details.""", bold=True)


@cli.command()
@click.option('-p', '--provider', help='Provider name. (USGS, SciHub...)', required=True)
@click.option('-d', '--dataset', help='Dataset name', required=True)
@click.option('-b', '--bbox', help='Bounding Box (west, south, east, north)', required=True)
@click.option('-t', '--time', help='Time start/end', required=True)
@click.option('-u', '--username', help='User', required=False)
@click.option('--password', help='Password (if needed)', required=False)
@click.option('--platform', help='Platform sensor (if required)', required=False)
@click.option('-o', '--output', help='Output to a file', type=click.Path(dir_okay=True), required=False)
@click.option('--config', help='Path to the Provider configuration file', type=click.Path(exists=True, readable=True), required=False)
@with_appcontext
def search(provider, dataset, bbox, time, username=None, password=None, config=None, **kwargs):
    """Search for data set in the given provider.

    Args:
        provider - Provider name to search.
        dataset - Data set name in provider.
        bbox - Bounding box definition (west, south, east, north).
        time - Time interval. (start/end). Format should be (YYYY-mm-dd)
        username - Optional username used to search in provider.
        password - Optional password used to search in provider.
        config - Optional Provider configuration file.
    """
    context = locals()

    # Get BDC-Collectors extension and then seek for provider support.
    ext = current_app.extensions['bdc_collector']

    provider_class = ext.get_provider(provider)

    if provider_class is None:
        raise RuntimeError(f'Provider {provider} not supported.')

    p = _make_provider(provider_class, username, password, config)

    bbox = [float(elm) for elm in bbox.split(',')]

    output = kwargs.pop('output', None)

    times = time.split('/')

    start_date, end_date = times
    if kwargs.get("platform") is None:
        kwargs.pop("platform", None)

    res = p.search(query=dataset, bbox=bbox, start_date=start_date, end_date=end_date, **kwargs)

    click.secho(f'Total scenes found: {len(res)}')

    for scene in res:
        click.secho(f'\t{scene.scene_id}')

    if output:
        click.secho(f'Saving output in {output}')

        file_path = Path(output)

        file_path.parent.mkdir(exist_ok=True, parents=True)

        with file_path.open('w') as f:
            context.pop('username', None)
            context.pop('password', None)

            f.write(json.dumps(
                dict(
                    total=len(res),
                    query=context,
                    result=res
                ),
                indent=4
            ))


@cli.command()
@click.option('-p', '--provider', required=True)
@click.option('-s', '--scene-id', help='Scene Identifier', required=True)
@click.option('-o', '--output', help='Save output directory', required=True)
@click.option('-d', '--dataset', help='Data set', required=False)
@click.option('-u', '--username', help='User', required=False)
@click.option('-P', '--password', help='Password (if needed)', required=False)
@click.option('--config', help='Path to the Provider configuration file', type=click.Path(exists=True, readable=True), required=False)
@with_appcontext
def download(provider, scene_id, output, config=None, **kwargs):
    """Search for data set in the given provider.

    Args:
        provider - Provider name to search.
        scene_id - Scene Id to download.
        output - Directory to save
        dataset - Optional data set name
        username - Optional username used to download from provider.
        password - Optional password used to download from provider.
    """
    ext = current_app.extensions['bdc_collector']

    provider_class = ext.get_provider(provider)

    kwargs.setdefault('progress', True)

    p = _make_provider(provider_class, config=config, **kwargs)

    result = p.download(scene_id, output=output, force=False, **kwargs)

    click.secho(f'File saved in {result}')


@cli.command()
@with_appcontext
def show_providers():
    """List the supported providers of BDC-Collectors."""
    ext = current_app.extensions['bdc_collector']

    click.secho('Supported providers: ', bold=True, fg='green')
    for provider_name in ext.list_providers():
        click.secho(f'\t{provider_name}', bold=True, fg='green')


def main(as_module=False):
    """Load Brazil Data Cube (bdc_collection_builder) as module."""
    import sys
    cli.main(args=sys.argv[1:], prog_name="python -m bdc_collectors" if as_module else None)


def _make_provider(provider_cls, username=None, password=None, config=None, **kwargs):
    options = {}
    if username and password:
        options.update(username=username, password=password, progress=True)
    elif config:
        with open(config) as fd:
            config_data = json.load(fd)
            options.update(config_data)
    return provider_cls(**options)