# pylint: disable=missing-module-docstring
# flake8: noqa
#
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
CARS cluster module init file
"""

# CARS imports
from cars.orchestrator.cluster.abstract_cluster import AbstractCluster

from . import (
    abstract_dask_cluster,
    local_dask_cluster,
    multiprocessing_cluster,
    pbs_dask_cluster,
    sequential_cluster,
)