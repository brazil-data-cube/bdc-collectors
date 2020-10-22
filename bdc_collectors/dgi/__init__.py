#
# This file is part of BDC-Collectors.
# Copyright (C) 2020 INPE.
#
# BDC-Collectors is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Driver for Access Data on DGI Server."""

import shutil
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List, Tuple, Type
from urllib.parse import urljoin

from ..base import BaseCollection, BaseProvider, SceneParser, SceneResult
from .api import API
from .collections import FireRisk, Precipitation, RelativeHumidity, Temperature
from .parser import DGICommonScene, DGITemperatureUmidScene


def init_provider():
    """Init provider factory loader."""
    return dict(DGI=DGI)


class DGI(BaseProvider):
    """Define a simple abstraction for consume data from FTP DGI server."""

    def __init__(self, **kwargs):
        """Build a data provider DGI instance."""
        self.kwargs = kwargs
        self.api = API(kwargs['username'], kwargs['password'])
        self.progress = kwargs.get('progress')
        self.collections[FireRisk.remote_path] = FireRisk
        self.collections[Precipitation.remote_path] = Precipitation
        self.collections[RelativeHumidity.remote_path] = RelativeHumidity
        self.collections[Temperature.remote_path] = Temperature

    def search(self, query, *args, **kwargs) -> List[SceneResult]:
        """Search for files on DGI server."""
        files = self.api.search(path=query)

        start_date = datetime.min
        end_date = datetime.max

        if 'start_date' in kwargs:
            start_date = datetime.fromisoformat(kwargs['start_date'])

        if 'end_date' in kwargs:
            end_date = datetime.fromisoformat(kwargs['end_date'])

        output = []

        for f in files:
            result = SceneResult(
                scene_id=Path(f).stem,
                cloud_cover=None,
                relative=f,
                link=urljoin(f'ftp://{self.api.host}', f)
            )

            parser_type, collection_type = self._guess_parser(result.scene_id)

            parser = parser_type(result.scene_id)

            if start_date <= parser.sensing_date() <= end_date:
                output.append(result)

        return output

    def _guess_parser(self, scene_id: str) -> Tuple[Type[SceneParser], BaseCollection]:
        """Retrieve the respective parser for scene_id (usually file_name)."""
        if scene_id.startswith('RF'):
            return DGICommonScene, FireRisk
        elif scene_id.startswith('PREC'):
            return DGICommonScene, Precipitation
        elif scene_id.startswith('RH2M'):
            return DGITemperatureUmidScene, RelativeHumidity
        elif scene_id.startswith('PREC'):
            return DGITemperatureUmidScene, Temperature

        raise RuntimeError(f'Not supported {scene_id}')

    def download(self, scene_id: str, *args, **kwargs) -> str:
        """Download files from DGI Server."""
        output = kwargs['output']

        parser, collection_t = self._guess_parser(scene_id)

        with TemporaryDirectory() as tmp:
            tmp_file = self.api.download(collection_t.remote_path, f'{scene_id}{collection_t.format}', output=tmp)

            expected_path = Path(output) / Path(tmp_file).name

            if expected_path.exists() and expected_path.is_file():
                expected_path.unlink()

            shutil.move(str(tmp_file), output)

            output = str(expected_path)

        return output
