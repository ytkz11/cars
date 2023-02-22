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
Helpers shared testing generic module:
contains global shared generic functions for tests/*.py
TODO: Try to put the most part in cars source code (if pertinent) and
organized functionnally.
TODO: add conftest.py general tests conf with tests refactor.
"""

import json
import logging

# Standard imports
import os

# Third party imports
import numpy as np
import pandas
import pandora
import rasterio as rio
import xarray as xr
from pandora.check_json import (
    check_pipeline_section,
    concat_conf,
    get_config_pipeline,
)
from pandora.state_machine import PandoraMachine

from cars.applications.dense_matching.loaders.pandora_loader import (
    check_input_section_custom_cars,
    get_config_input_custom_cars,
)

# CARS imports
from cars.core import constants as cst
from cars.core import constants_disparity as cst_disp
from cars.pipelines.sensor_to_full_resolution_dsm import sensors_inputs

# Specific values
# 0 = valid pixels
# 255 = value used as no data during the resampling in the epipolar geometry
PROTECTED_VALUES = [255]


def cars_path():
    """
    Return root of cars source directory
    One level down from tests
    """
    return os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


def generate_input_json(
    input_json,
    out_dir,
    pipeline,
    orchestrator_mode,
    orchestrator_parameters=None,
):
    """
    Load a partially filled input.json, fill it with out_dir
    and orchestrator mode, and transform relative path to
     absolute paths. Generates a new json dumped in out_dir

    :param input_json: input json
    :type input_json: str
    :param out_dir: absolute path out directory
    :type out_dir: str
    :param pipeline: pipeline to run
    :type pipeline: str
    :param orchestrator_mode: orchestrator mode
    :type orchestrator_mode: str
    :param orchestrator_parameters: advanced orchestrator params
    :type orchestrator_parameters: dict

    :return: path of generated json, dict input config
    :rtype: str, dict
    """
    # Load dict
    json_dir_path = os.path.dirname(input_json)
    with open(input_json, "r", encoding="utf8") as fstream:
        config = json.load(fstream)
    # Overload orchestrator
    config["orchestrator"] = {"mode": orchestrator_mode}
    if orchestrator_parameters is not None:
        config["orchestrator"].update(orchestrator_parameters)
    # Overload out_dir
    config["output"] = {"out_dir": os.path.join(out_dir, "output")}

    # overload pipeline
    config["pipeline"] = pipeline

    # Create keys
    if "applications" not in config:
        config["applications"] = {}

    # transform paths
    new_config = config.copy()
    check_epipolar_a_priori = True

    if pipeline == "sensor_to_low_resolution_dsm":
        check_epipolar_a_priori = False
    new_config["inputs"] = sensors_inputs.sensors_check_inputs(
        new_config["inputs"],
        config_json_dir=json_dir_path,
        check_epipolar_a_priori=check_epipolar_a_priori,
    )

    # dump json
    new_json_path = os.path.join(out_dir, "new_input.json")
    with open(new_json_path, "w", encoding="utf8") as fstream:
        json.dump(new_config, fstream, indent=2)

    return new_json_path, new_config


def absolute_data_path(data_path):
    """
    Return a full absolute path to test data
    environment variable.
    """
    data_folder = os.path.join(os.path.dirname(__file__), "data")
    return os.path.join(data_folder, data_path)


def get_geoid_path():
    return os.path.join(cars_path(), "cars/conf/geoid/egm96.grd")


def get_geometry_loader():
    return "OTBGeometry"


def temporary_dir():
    """
    Returns path to temporary dir from CARS_TEST_TEMPORARY_DIR environment
    variable. Defaults to /tmp
    """
    if "CARS_TEST_TEMPORARY_DIR" not in os.environ:
        # return default tmp dir
        return "/tmp"
    # return env defined tmp dir
    return os.environ["CARS_TEST_TEMPORARY_DIR"]


def assert_same_images(actual, expected, rtol=0, atol=0):
    """
    Compare two image files with assertion:
    * same height, width, transform, crs
    * assert_allclose() on numpy buffers
    """
    with rio.open(actual) as rio_actual:
        with rio.open(expected) as rio_expected:
            np.testing.assert_equal(rio_actual.width, rio_expected.width)
            np.testing.assert_equal(rio_actual.height, rio_expected.height)
            assert rio_actual.transform == rio_expected.transform
            assert rio_actual.crs == rio_expected.crs
            assert rio_actual.nodata == rio_expected.nodata
            np.testing.assert_allclose(
                rio_actual.read(), rio_expected.read(), rtol=rtol, atol=atol
            )


def assert_same_carsdatasets(actual, expected, rtol=0, atol=0):
    """
    Compare two Carsdatasets:
    """
    assert (
        list(actual.attributes.keys()).sort()
        == list(expected.attributes.keys()).sort()
    )
    for key in expected.attributes.keys():
        if isinstance(expected.attributes[key], np.ndarray):
            np.testing.assert_allclose(
                actual.attributes[key], expected.attributes[key]
            )
        else:
            assert actual.attributes[key] == expected.attributes[key]

    assert actual.shape == expected.shape
    assert actual.tiling_grid.size == expected.tiling_grid.size
    assert actual.overlaps.size == expected.overlaps.size
    assert list(actual.tiling_grid).sort() == list(expected.tiling_grid).sort()
    assert list(actual.overlaps).sort() == list(expected.overlaps).sort()
    for idx, actual_tiles in enumerate(actual.tiles):
        assert len(actual_tiles) == len(expected.tiles[idx])
        for idx_tile, actual_tile in enumerate(actual_tiles):
            if isinstance(actual_tile, np.ndarray):
                np.testing.assert_allclose(
                    actual_tile,
                    expected.tiles[idx][idx_tile],
                    rtol,
                    atol,
                )
            elif isinstance(actual_tile, xr.Dataset):
                assert_same_datasets(
                    actual_tile, expected.tiles[idx][idx_tile], rtol, atol
                )
            elif isinstance(actual_tile, xr.DataArray):
                assert_same_datasets(
                    actual_tile, expected.tiles[idx][idx_tile], rtol, atol
                )
            elif isinstance(actual_tile, pandas.Dataframe):
                assert_same_dataframes(
                    actual_tile, expected.tiles[idx][idx_tile], rtol, atol
                )
            elif isinstance(actual_tile, dict):
                assert all(
                    (
                        expected.tiles[idx][idx_tile].get(k) == v
                        for k, v in actual_tile.items()
                    )
                )
            else:
                logging.error(
                    "the tile format unsupported by helper.py: {}".format(
                        type(actual_tile)
                    )
                )


def assert_same_datasets(actual, expected, rtol=0, atol=0):
    """
    Compare two datasets:
    """
    assert (
        list(actual.attrs.keys()).sort() == list(expected.attrs.keys()).sort()
    )
    for key in expected.attrs.keys():
        if isinstance(expected.attrs[key], np.ndarray):
            np.testing.assert_allclose(actual.attrs[key], expected.attrs[key])
        else:
            assert actual.attrs[key] == expected.attrs[key]
    assert actual.dims == expected.dims
    assert (
        list(actual.coords.keys()).sort() == list(expected.coords.keys()).sort()
    )
    for key in expected.coords.keys():
        np.testing.assert_allclose(
            actual.coords[key].values, expected.coords[key].values
        )
    assert (
        list(actual.data_vars.keys()).sort()
        == list(expected.data_vars.keys()).sort()
    )
    for key in expected.data_vars.keys():
        np.testing.assert_allclose(
            actual[key].values, expected[key].values, rtol=rtol, atol=atol
        )


def assert_same_dataframes(actual, expected, rtol=0, atol=0):
    """
    Compare two dataframes:
    """
    assert (
        list(actual.attrs.keys()).sort() == list(expected.attrs.keys()).sort()
    )
    for key in expected.attrs.keys():
        if isinstance(expected.attrs[key], np.ndarray):
            np.testing.assert_allclose(actual.attrs[key], expected.attrs[key])
        else:
            assert actual.attrs[key] == expected.attrs[key]
    assert list(actual.keys()).sort() == list(expected.keys()).sort()
    np.testing.assert_allclose(
        actual.to_numpy(), expected.to_numpy(), rtol=rtol, atol=atol
    )


def add_color(dataset, color_array, color_mask=None, margin=None):
    """ " Add color array to xarray dataset"""

    new_dataset = dataset.copy(deep=True)

    if margin is None:
        margin = [0, 0, 0, 0]

    if cst.EPI_IMAGE in dataset:
        nb_row = dataset[cst.EPI_IMAGE].values.shape[0]
        nb_col = dataset[cst.EPI_IMAGE].values.shape[1]
    elif cst_disp.MAP in dataset:
        nb_row = dataset[cst_disp.MAP].values.shape[0]
        nb_col = dataset[cst_disp.MAP].values.shape[1]
    elif cst.X in dataset:
        nb_row = dataset[cst.X].values.shape[0]
        nb_col = dataset[cst.X].values.shape[1]
    else:
        logging.error("nb_row and nb_col not set")
        nb_row = color_array.shape[-2] + margin[1] + margin[3]
        nb_col = color_array.shape[-1] + margin[0] + margin[2]

    # add color
    if len(color_array.shape) > 2:
        nb_band = color_array.shape[0]
        if margin is None:
            new_color_array = color_array
        else:
            new_color_array = np.zeros([nb_band, nb_row, nb_col])
            new_color_array[
                :,
                margin[1] : nb_row - margin[3],
                margin[0] : nb_col - margin[2],
            ] = color_array
        # multiple bands
        if cst.BAND not in new_dataset.dims:
            nb_bands = color_array.shape[0]
            new_dataset.assign_coords({cst.BAND: np.arange(nb_bands)})

        new_dataset[cst.EPI_COLOR] = xr.DataArray(
            new_color_array,
            dims=[cst.BAND, cst.ROW, cst.COL],
        )
    else:
        if margin is None:
            new_color_array = color_array
        else:
            new_color_array = np.zeros([nb_row, nb_col])
            new_color_array[
                margin[1] : nb_row - margin[3], margin[0] : nb_col - margin[2]
            ] = color_array
        new_dataset[cst.EPI_COLOR] = xr.DataArray(
            new_color_array,
            dims=[cst.ROW, cst.COL],
        )

    if color_mask is not None:
        new_color_mask = np.zeros([nb_row, nb_col])
        new_color_mask[
            margin[1] : nb_row - margin[3], margin[0] : nb_col - margin[2]
        ] = color_mask

        new_dataset[cst.EPI_COLOR_MSK] = xr.DataArray(
            new_color_mask,
            dims=[cst.ROW, cst.COL],
        )

    return new_dataset


def create_corr_conf(user_cfg):
    """
    Create correlator configuration for stereo testing
    TODO: put in CARS source code ? (external?)
    """

    # Import plugins before checking configuration
    pandora.import_plugin()
    # Check configuration and update the configuration with default values
    # Instantiate pandora state machine
    pandora_machine = PandoraMachine()
    # check pipeline
    user_cfg_pipeline = get_config_pipeline(user_cfg)
    cfg_pipeline = check_pipeline_section(user_cfg_pipeline, pandora_machine)
    # check a part of input section
    user_cfg_input = get_config_input_custom_cars(user_cfg)
    cfg_input = check_input_section_custom_cars(user_cfg_input)
    # concatenate updated config
    cfg = concat_conf([cfg_input, cfg_pipeline])
    return cfg


def corr_conf_defaut():
    """
    Provide pandora default configuration for test
    """
    user_cfg = {}
    with open(
        absolute_data_path(os.path.join("conf_pandora", "conf_default.json")),
        "r",
        encoding="utf8",
    ) as fstream:
        user_cfg = json.load(fstream)
    return user_cfg


def corr_conf_with_confidence():
    """
    Provide pandora configuration with confidence option
    """
    user_cfg = {}
    with open(
        absolute_data_path(
            os.path.join("conf_pandora", "conf_with_all_confidences.json")
        ),
        "r",
        encoding="utf8",
    ) as fstream:
        user_cfg = json.load(fstream)
    return user_cfg
