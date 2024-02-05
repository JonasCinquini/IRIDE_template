#!/usr/bin/env python
""" Unit tests for distribute_ps_grid.py. """

import os
import pytest
import time
import dask_geopandas as dgpd
from distribute_ps_grid import distribute_ps_grid


def test_distribute_ps_grid():
    # - import sample data
    input_file \
        = os.path.join('.', 'data', 'shapefiles',
                       'csk_ps_sample_Nocera_Terinese_A_epsg4326.shp')

    # - Import CSK Along Track Grid
    grid_file \
        = os.path.join('.', 'data', 'shapefiles',
                       'grid_CSG2_151_STR-007_ASC.shp')
    # -  Call the function
    result = distribute_ps_grid(input_file, grid_file)

    # Assertions based on your expected results
    assert isinstance(result, dgpd.GeoDataFrame)


def test_invalid_files():
    with pytest.raises(FileNotFoundError):
        distribute_ps_grid("nonexistent_file.shp", "grid_file.shp")


def test_large_dataset_performance():
    # Create GeoDataFrames for testing
    start_time = time.time()
    # - import sample data
    input_file \
        = os.path.join('.', 'data', 'shapefiles',
                       'csk_ps_sample_Nocera_Terinese_A_epsg4326.shp')

    # - Import CSK Along Track Grid
    grid_file \
        = os.path.join('.', 'data', 'shapefiles',
                       'grid_CSG2_151_STR-007_ASC.shp')
    # -  Call the function
    _ = distribute_ps_grid(input_file, grid_file)

    end_time = time.time()

    # Set a reasonable threshold based on your performance expectations
    assert end_time - start_time < 1    # seconds
