#
# This file is part of BDC-Collectors.
# Copyright (C) 2020 INPE.
#
# BDC-Collectors is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Define the common exceptions for Data Download."""


class DownloadError(Exception):
    """Generic error for Download."""

    message: str

    def __init__(self, message):
        """Build a DownloadError instance."""
        self.message = message

    def __str__(self):
        """Retrieve the string representation of DownloadError."""
        return f'DownloadError, {self.message}'


class DataOfflineError(DownloadError):
    """Indicate that the scene_id is not available (Offline).

    Frequently used by Sentinel SciHub Provider.
    """

    scene_id: str

    def __init__(self, scene_id):
        """Create a DataOfflineError."""
        super().__init__(f'Scene {scene_id} is offline/not available')

        self.scene_id = scene_id

    def __str__(self):
        """Define the string representation for DataOfflineError."""
        return f'DataOfflineError(scene_id={self.scene_id})'
