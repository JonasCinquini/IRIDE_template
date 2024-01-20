#!/usr/bin/env python
u"""
Written by Enrico Ciraci'
January 2024

Set of Classes to compute and process a line passing through two points.
"""
# - Python Dependencies
import numpy as np


class PtsLine:
    """
    Class to compute the equation of a line passing through two points.
    """
    def __init__(self, x1: float, y1: float,
                 x2: float, y2: float) -> None:
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.m = (y2 - y1) / (x2 - x1)
        self.q = y1 - (self.m * x1)

    def y(self, x: float | np.ndarray) -> float | np.ndarray:
        return self.m * x + self.q

    def x(self, y: float | np.ndarray) -> float | np.ndarray:
        return (y - self.q) / self.m


class PtsLineIntersect:
    """
    Class to compute the intersection point of two lines passing through
    two points.
    """
    def __init__(self, line_1: PtsLine, line_2: PtsLine) -> None:
        self.m1 = line_1.m
        self.q1 = line_1.q
        self.m2 = line_2.m
        self.q2 = line_2.q

    def intersect(self) -> tuple[float, float]:
        x = (self.q2 - self.q1) / (self.m1 - self.m2)
        y = self.m1 * x + self.q1
        return x, y

