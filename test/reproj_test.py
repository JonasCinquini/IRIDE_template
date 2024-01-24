#!/usr/bin/env python
""" Unit tests for the reproject_geometry function. """
import pytest
from shapely.geometry import Point, Polygon
from reproject_geometry import reproject_geometry

@pytest.fixture
def example_polygon():
    """Return a square polygon."""
    return Polygon([(0, 0), (0, 1), (1, 1), (1, 0)])

@pytest.fixture
def example_point():
    """Return a point in the center of the square polygon."""
    return Point(0.5, 0.5)


def test_reproject_geometry_polygon(example_polygon):
    """Test the reproject_geometry function with a polygon."""
    result \
        = reproject_geometry(example_polygon, 4326, 3857)
    assert isinstance(result, Polygon)


def test_reproject_geometry_point(example_point):
    """Test the reproject_geometry function with a point."""
    result \
        = reproject_geometry(example_point,4326, 3857)
    assert isinstance(result, Point)