#!/usr/bin/env python
# coding: utf8
#
# Copyright (c) 2020 Centre National d'Etudes Spatiales (CNES).
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
Test module for cars/pipelines/wrappers.py
Important : Uses conftest.py for shared pytest fixtures
"""


import pickle

# Third party imports
import pytest

# CARS imports
import cars.applications.dense_matching.dense_matching_tools as dense_match
from cars.applications.dense_matching.census_mccnn_sgm import compute_disparity
from cars.applications.resampling.bicubic_resampling import (
    generate_epipolar_images_wrapper,
)
from cars.applications.triangulation.line_of_sight_intersection import (
    compute_points_cloud,
)
from cars.conf import input_parameters as in_params

# CARS Tests imports
from ..helpers import (
    absolute_data_path,
    assert_same_datasets,
    corr_conf_defaut,
    create_corr_conf,
)


@pytest.mark.unit_tests
def test_epipolar_pipeline(
    images_and_grids_conf,
    color1_conf,  # pylint: disable=redefined-outer-name
    no_data_conf,
    disparities_conf,  # pylint: disable=redefined-outer-name
    epipolar_origins_spacings_conf,  # pylint: disable=redefined-outer-name
    epipolar_sizes_conf,
):  # pylint: disable=redefined-outer-name
    """
    Test images_pair_to_3d_points on ventoux dataset (epipolar geometry)
    with Pandora
    Note: Fixtures parameters are set and shared in conftest.py
    """
    # With nodata and color
    configuration = images_and_grids_conf
    configuration["input"].update(color1_conf["input"])
    configuration["input"].update(no_data_conf["input"])
    configuration["preprocessing"]["output"].update(
        epipolar_sizes_conf["preprocessing"]["output"]
    )
    configuration["preprocessing"]["output"].update(
        epipolar_origins_spacings_conf["preprocessing"]["output"]
    )
    configuration["preprocessing"]["output"].update(
        disparities_conf["preprocessing"]["output"]
    )

    region = [420, 200, 530, 320]
    # Pandora configuration
    corr_cfg = corr_conf_defaut()
    corr_cfg = create_corr_conf(corr_cfg)

    initial_margins = dense_match.get_margins(-13, 14, corr_cfg)
    pandora_margins = initial_margins["left_margin"].values

    # overlaps are directly margins because current region is in the center
    overlaps = {
        "left": pandora_margins[0],
        "up": pandora_margins[1],
        "right": pandora_margins[2],
        "down": pandora_margins[3],
    }

    window = {
        "col_min": region[0],
        "row_min": region[1],
        "col_max": region[2],
        "row_max": region[3],
    }

    # retrieves some data
    epipolar_size_x = configuration["preprocessing"]["output"][
        "epipolar_size_x"
    ]
    epipolar_size_y = configuration["preprocessing"]["output"][
        "epipolar_size_y"
    ]
    img1 = configuration["input"][in_params.IMG1_TAG]
    img2 = configuration["input"][in_params.IMG2_TAG]
    color1 = configuration["input"].get(in_params.COLOR1_TAG, None)
    grid1 = configuration["preprocessing"]["output"]["left_epipolar_grid"]
    grid2 = configuration["preprocessing"]["output"]["right_epipolar_grid"]
    nodata1 = configuration["input"].get(in_params.NODATA1_TAG, None)
    nodata2 = configuration["input"].get(in_params.NODATA2_TAG, None)
    mask1 = configuration["input"].get(in_params.MASK1_TAG, None)
    mask2 = configuration["input"].get(in_params.MASK2_TAG, None)

    left_image, right_image = generate_epipolar_images_wrapper(
        overlaps,
        overlaps,
        window,
        initial_margins,
        epipolar_size_x,
        epipolar_size_y,
        img1,
        img2,
        grid1,
        grid2,
        add_color=True,
        color1=color1,
        mask1=mask1,
        mask2=mask2,
        nodata1=nodata1,
        nodata2=nodata2,
    )

    disp_map = compute_disparity(
        left_image,
        right_image,
        corr_cfg,
    )

    points_cloud = compute_points_cloud(
        left_image,
        disp_map,
        configuration,
        "OTBGeometry",
        32636,
        add_msk_info=True,
    )

    # Uncomment to update reference
    # with open(
    #     absolute_data_path("ref_output/cloud1_ref_pandora"), "wb"
    # ) as points_cloud_file:
    #     pickle.dump(points_cloud, points_cloud_file)

    with open(
        absolute_data_path("ref_output/cloud1_ref_pandora"), "rb"
    ) as points_cloud_file:
        ref_pc = pickle.load(points_cloud_file)
        assert_same_datasets(points_cloud, ref_pc, atol=1.0e-3)
