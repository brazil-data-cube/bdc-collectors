#
# This file is part of BDC-Collectors.
# Copyright (C) 2020 INPE.
#
# BDC-Collectors is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Define the data set of Google for Sentinel products."""

import shutil
from pathlib import Path

from ..scihub.parser import Sentinel2Scene
from ..utils import working_directory


class GoogleSentinel:
    """Define the Sentinel product definition."""

    bucket = 'gcp-public-data-sentinel-2'

    def __init__(self, scene_id: str):
        """Create the GoogleSentinel instance."""
        self.parser = Sentinel2Scene(scene_id)
        self.keep_folder = True

    @property
    def folder(self):
        """Retrieve base folder of Sentinel."""
        return f'{self.parser.scene_id}.SAFE'

    def get_url(self) -> str:
        """Get the relative URL path in the Sentinel bucket."""
        source = self.parser.source()
        tile = self.parser.tile_id()
        scene_id = self.parser.scene_id

        # TODO: Add support to download L2. We should just append L2 when MSIL2A found.

        return f'tiles/{tile[:2]}/{tile[2]}/{tile[-2:]}/{scene_id}.SAFE'

    def apply_processing(self, file_path):
        """Apply a function in post download processing."""
        pass

    def process(self, downloaded_files: list, output: str) -> str:
        """Compress the downloaded files into scene.zip."""
        with working_directory(output):
            file_name = shutil.make_archive(
                base_dir=self.folder,
                format='zip',
                base_name=self.parser.scene_id
            )
        # Remove .SAFE folder
        shutil.rmtree(str(Path(output) / self.folder))

        return str(Path(output) / file_name)
