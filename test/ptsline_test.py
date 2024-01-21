#!/usr/bin/env python
"""
Unit tests for the PtsLine and PtsLineIntersect classes.
"""
import pytest
import numpy as np
from PtsLine import PtsLine, PtsLineIntersect

@pytest.fixture
def example_lines():
    """Return two lines that intersect at (1, 1)."""
    line1 = PtsLine(0, 0, 2, 2)
    line2 = PtsLine(0, 2, 2, 0)
    return line1, line2


def test_pts_line_y_val():
    """Test the y_val method of the PtsLine class."""
    line = PtsLine(0, 0, 2, 2)
    assert line.y_val(1) == 1


def test_pts_line_x_val():
    """Test the x_val method of the PtsLine class."""
    line = PtsLine(0, 0, 2, 2)
    assert line.x_val(1) == 1


def test_pts_line_intersect(example_lines):
    """Test the intersection property of the PtsLineIntersect class."""
    line1, line2 = example_lines
    intersect = PtsLineIntersect(line1, line2)
    assert np.allclose(intersect.intersection, (1, 1))


def test_parallel_lines():
    line1 = PtsLine(0, 0, 2, 2)
    line2 = PtsLine(1, 1, 3, 3)
    intersect = PtsLineIntersect(line1, line2)
    assert intersect.intersection == (None, None)