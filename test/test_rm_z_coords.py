#!/usr/bin/env python
""" Unit tests for the rm_z_coord function. """
import geopandas as gpd
from shapely.geometry import Polygon
from rm_z_coord import rm_z_coord


def test_rm_z_coord():
    # Create a GeoDataFrame for testing
    data = {'geometry': [Polygon([(0, 0, 1), (1, 0, 2),
                                  (1, 1, 3), (0, 1, 4)])]}
    gdf = gpd.GeoDataFrame(data, crs='EPSG:4326')

    # Apply the function
    result_gdf = rm_z_coord(gdf.copy())

    # Check if the z-coordinate is removed from the geometry
    assert all(result_gdf['geometry'].apply(lambda geom:
                                            len(geom.exterior.coords[0]) == 2))
