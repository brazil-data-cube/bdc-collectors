#
# This file is part of BDC-Collectors.
# Copyright (C) 2020 INPE.
#
# BDC-Collectors is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Driver for Access Data on DGI Server."""
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List, Optional, Tuple, Type
from urllib.parse import urljoin

from ..base import BaseCollection, BaseProvider, SceneResult
from .api import API
from .collections import DGICollection
from .parser import DGICommonScene


def init_provider():
    """Init provider factory loader."""
    return dict(DGI=DGI)


MatchedItem = Tuple[str, Optional[datetime]]


class DGI(BaseProvider):
    """Define a simple abstraction for consume data from FTP DGI server."""

    def __init__(self, **kwargs):
        """Build a data provider DGI instance."""
        self.kwargs = kwargs
        self.api = API(kwargs['username'], kwargs['password'], kwargs['host'])
        self.progress = kwargs.get('progress')

    def get_collector(self, collection: str) -> Type[BaseCollection]:
        """Retrieve the supported collections of DGI server."""
        collection_type = DGICollection
        collection_type.pattern = collection

        return collection_type

    def get_folders(self, base_paths, mask, context, **kwargs) -> List[MatchedItem]:
        """List folders on remote server recursively, trying to match with given mask."""
        mask_list = mask

        folders = []

        if isinstance(mask, str):
            mask_list = Path(mask).parents.parts

        for entry in base_paths:
            dirs = self.api.search(str(entry))

            if len(dirs) == 0:
                continue

            for found_dir in dirs:
                merged = str(mask_list[0])

                if context != '.':
                    merged = os.path.join(context, merged)

                matched = self.mask_matches(found_dir, merged, **kwargs)

                if matched:
                    if len(mask_list) == 1:
                        folders.append((found_dir, matched))
                        continue

                    internal = self.get_folders([found_dir], mask_list[1:], found_dir, **kwargs)

                    if internal:
                        folders.extend(internal)

        return folders

    def mask_matches(self, folder: str, mask: str, start: datetime = datetime.min, end: datetime = datetime.max) -> bool:
        """Try to match the folder with mask on remote file."""
        pattern = self.get_regex(mask)

        matched = re.match(pattern, folder)

        if not matched:
            return False

        dtime = self.get_date_time(folder, mask)

        if not dtime:
            return True

        if dtime < start or dtime > end:
            return False

        return dtime

    @staticmethod
    def get_regex(mask: str):
        """Parse the folder mask to the supported REGEX values."""
        output_mask = mask
        output_mask = output_mask.replace('%Y', '(?P<YEAR2DIGITS>[0-9]{4})')
        output_mask = output_mask.replace('%m', '(?P<MONTH>0[1-9]|1[012])')
        output_mask = output_mask.replace('%d', '(?P<DAY>0[1-9]|[12][0-9]|3[01])')
        output_mask = output_mask.replace('%JJJ', '(?P<JULIAN_DAY>\\d{3})')
        output_mask = output_mask.replace('%H', '(?P<HOUR>[0-1][0-9]|2[0-4])')
        output_mask = output_mask.replace('%M', '(?P<MINUTES>[0-5][0-9])')
        output_mask = output_mask.replace('%S', '(?P<SECONDS>[0-5][0-9])')
        output_mask = output_mask.replace('%YY', '(?P<YEAR2DIGITS>[0-9]{2})')
        output_mask = output_mask.replace('*', '.*')
        output_mask += '(?P<EXTENSIONS>(\.(gz|zip|rar|7z|tar))+)?$'

        return output_mask

    @staticmethod
    def get_date_time(folder, mask) -> Optional[datetime]:
        """Try to get a date time value from entry."""
        pattern = DGI.get_regex(mask)

        matched = re.match(pattern, folder)

        if not matched:
            return None

        groups = matched.groupdict()
        date_str = ''
        date_mask = ''

        if groups.get('YEAR') or groups.get('YEAR2DIGITS'):
            date_str += groups.get('YEAR') or groups.get('YEAR2DIGITS')
            date_mask = '%Y'

        if groups.get('JULIAN_DAY'):
            date_str += groups['JULIAN_DAY']
            date_mask += '%j'

        if groups.get('MONTH'):
            date_str += groups['MONTH']
            date_mask += '%m'

        if groups.get('DAY'):
            date_str += groups['DAY']
            date_mask += '%d'

        if not date_mask:
            return None

        res = datetime.strptime(date_str, date_mask)

        return res

    def resolve_path(self, folder_mask: Path, context='.', **kwargs):
        """Try to match the folder mask with remote files."""
        mask_list = folder_mask.parts

        if len(mask_list) == 0:
            return []

        initial_paths = [context]

        paths = self.get_folders(initial_paths, mask_list, context, **kwargs)

        return paths

    def search(self, query, *args, **kwargs) -> List[SceneResult]:
        """Search for files on DGI server."""
        mask = query

        options = dict()

        if 'start_date' in kwargs:
            options['start'] = datetime.fromisoformat(kwargs['start_date'])

        if 'end_date' in kwargs:
            options['end'] = datetime.fromisoformat(kwargs['end_date'])

        files = self.resolve_path(Path(mask), **options)

        if len(files) == 0:
            return []

        # TODO: When mask is not given, we should validate since it will map root folder as a sceneid.

        return [
            SceneResult(
                scene_id=Path(f[0]).stem,
                cloud_cover=None,
                relative=f[0],
                datetime=f[-1],
                link=urljoin(f'ftp://{self.api.host}', f[0])
            ) for f in files
        ]

    def download(self, scene_id: str, *args, **kwargs) -> str:
        """Download files from DGI Server."""
        output = kwargs['output']
        dataset = kwargs['dataset']

        files = self.resolve_path(Path(dataset))

        found = None

        for matched in files:
            if scene_id in matched[0]:
                found = matched

        if found is None:
            raise RuntimeError(f'Not found {scene_id} with {dataset}')

        with TemporaryDirectory() as tmp:
            tmp_file = self.api.download(found[0], output=tmp)

            expected_path = Path(output) / Path(tmp_file).name

            if expected_path.exists() and expected_path.is_file():
                expected_path.unlink()

            expected_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(tmp_file), output)

            output = str(expected_path)

        return output
