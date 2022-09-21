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

"""Demo package to emulate external Provider."""

from bdc_collectors.base import BaseProvider, SceneResult


def init_provider():
    """Register the DEMO provider."""
    return dict(
        DEMO=DEMO
    )


class DEMO(BaseProvider):
    """Define a simple abstraction of provider DEMO."""

    def search(self, query, *args, **kwargs):
        """Search for scenes."""
        return [SceneResult('theid', 100)]

    def download(self, scene_id: str, *args, **kwargs) -> str:
        """Pass."""