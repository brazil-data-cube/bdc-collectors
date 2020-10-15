#
# This file is part of BDC-Collectors.
# Copyright (C) 2020 INPE.
#
# BDC-Collectors is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
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