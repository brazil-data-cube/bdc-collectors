#
# This file is part of BDC-Collectors.
# Copyright (C) 2020 INPE.
#
# BDC-Collectors is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
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

    def download(self, path: str, file_name: str, output: str) -> str:
        """Download a single file from remote FTP server.

        Raises:
            DownloadError when any exception occurs.
        """
        try:
            remote_name = os.path.join(path, file_name)

            os.makedirs(output, exist_ok=True)

            output = os.path.join(output, file_name)

            with open(output, 'wb') as f:
                self.ftp.retrbinary(f'RETR {remote_name}', lambda data: f.write(data))

            return output
        except Exception as e:
            raise DownloadError(str(e))
