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

    Frequently used by Sentinel ``SciHub`` or ``Dataspace`` Provider.
    """

    scene_id: str

    def __init__(self, scene_id):
        """Create a DataOfflineError."""
        super().__init__(f'Scene {scene_id} is offline/not available')

        self.scene_id = scene_id

    def __str__(self):
        """Define the string representation for DataOfflineError."""
        return f'DataOfflineError(scene_id={self.scene_id})'
