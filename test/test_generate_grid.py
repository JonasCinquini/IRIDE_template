#!/usr/bin/env python
""" Unit tests for the generate_grid function. """
import geopandas as gpd
from shapely.geometry import Polygon
from generate_grid import generate_grid


def test_generate_grid():
    # Create a sample GeoDataFrame for testing
    d = {'index': 1,
         'geometry': Polygon([(12, 36), (11.5, 38), (14, 38.5),
                              (14, 36.5), (12, 36)])}
    gdf_t = gpd.GeoDataFrame(d, crs='EPSG:4326', index=[0])

    n_c = 3
    az_res = 5000
    buffer_dist = 1000

    # Ensure the function runs without errors
    result_gdf = generate_grid(gdf_t, n_c, az_res, buffer_dist)

    # Perform assertions based on your expectations for the result
    assert isinstance(result_gdf, gpd.GeoDataFrame)
    assert len(result_gdf) > 0
