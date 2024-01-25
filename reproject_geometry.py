#!/usr/bin/env python
"""
Written by Enrico Ciraci'
January 2024

Reproject a Shapely geometry.
"""
from shapely.geometry import Polygon, Point
from pyproj import CRS, Transformer
from shapely.ops import transform


def reproject_geometry(geometry: Polygon | Point,
                       source_epsg: int, target_epsg: int) -> Polygon | Point:
    """
    Reproject a Shapely geometry.
    Args:
        geometry: shapely.geometry.Polygon | shapely.geometry.Point
        source_epsg: source EPSG code
        target_epsg: target EPSG code

    Returns: shapely.geometry.Polygon | shapely.geometry.Point
    """
    # Set up coordinate reference systems
    target_crs = CRS.from_epsg(target_epsg)
    # Create a transformer for the coordinate transformation
    transformer = Transformer.from_crs(source_epsg, target_crs, always_xy=True)
    try:
        # - Polygon
        return geometry.apply(lambda geom:
                              transform(transformer.transform, geom))
    except AttributeError:
        # - Point
        return transform(transformer.transform, geometry)
