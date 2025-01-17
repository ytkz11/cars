#!/usr/bin/env python
# coding: utf8
#
# Copyright (c) 2023 Centre National d'Etudes Spatiales (CNES).
#
# This file is part of CARS
# (see https://github.com/CNES/cars).
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""
Test module for cars/core/geometry/shareloc_geometry.py
"""

# Third party imports
import pytest

# CARS imports
from cars.conf import input_parameters
from cars.core.geometry.shareloc_geometry import RPC_TYPE, SharelocGeometry

# CARS Tests imports
from ...helpers import absolute_data_path, get_geoid_path


@pytest.mark.unit_tests
def test_dir_loc_rpc():
    """
    Test direct localization with RPC
    """
    conf = {
        input_parameters.IMG1_TAG: absolute_data_path(
            "input/phr_ventoux/left_image.tif"
        ),
        input_parameters.MODEL1_TAG: absolute_data_path(
            "input/phr_ventoux/left_image.geom"
        ),
        input_parameters.MODEL1_TYPE_TAG: RPC_TYPE,
    }
    dem = absolute_data_path("input/phr_ventoux/srtm/N44E005.hgt")
    geoid = get_geoid_path()

    lat, lon, alt = SharelocGeometry.direct_loc(
        conf,
        input_parameters.PRODUCT1_KEY,
        0,
        0,
        dem=dem,
        geoid=geoid,
    )

    # test lat, lon, alt value
    # put decimal values to 10 to know if modifications are done.
    assert lat == pytest.approx(44.20805591262138, abs=1e-10)
    assert lon == pytest.approx(5.193409396203882, abs=1e-10)
    assert alt == pytest.approx(503.5502439683996, abs=1e-10)
