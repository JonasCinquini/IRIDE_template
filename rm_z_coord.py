#!/usr/bin/env python
import geopandas as gpd
from shapely.geometry import Polygon
"""
Written by Enrico Ciraci'
January 2024

Remove z coordinate from a GeoDataFrame.
Convert a GeoDataFrame with z coordinate to a GeoDataFrame
without z coordinate.
"""


def rm_z_coord(gdf) -> gpd.GeoDataFrame:
    """
    Remove z coordinate from a GeoDataFrame
    Args:
        gdf: GeoDataFrame

    Returns:

    """
    # - remove z coordinate
    no_z_coord = []
    for _, row in gdf.iterrows():
        # - remove z coordinate
        z_coords = row['geometry'].exterior.coords[:-1]
        no_z_coord.append(Polygon([(crd[0], crd[1]) for crd in z_coords]))
    gdf['geometry'] = no_z_coord

    return gdf
