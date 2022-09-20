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

"""Define the API for communication with DGI server."""

import ftplib
import os
from typing import List

from bdc_collectors.exceptions import DownloadError

_INVALID_PATHS = ('.', '..', )


class API:
    """Define a wrapper fro FTP that consumes the DGI server."""

    def __init__(self, username: str, password: str, host: str, **options):
        """Build a instance of ftp client."""
        self.ftp = ftplib.FTP(host=host, user=username, passwd=password, **options)
        self.kwargs = dict(username=username, password=password, host=host, **options)
        self.host = host

    def search(self, path: str) -> List[str]:
        """List all entries from a remote path."""
        try:
            entries = self.ftp.nlst(path)
        except ftplib.error_perm as e:
            if str(e) == '550 No files found':
                return []
            raise

        return [entry for entry in entries if os.path.basename(entry) not in _INVALID_PATHS]

    def download(self, entry: str, output: str) -> str:
        """Download a single file from remote FTP server.

        Raises:
            DownloadError when any exception occurs.
        """
        try:
            os.makedirs(output, exist_ok=True)

            output = os.path.join(output, os.path.basename(entry))

            with open(output, 'wb') as f:
                self.ftp.retrbinary(f'RETR {entry}', lambda data: f.write(data))

            return output
        except Exception as e:
            raise DownloadError(str(e))
