#!/usr/bin/env python
u"""
Written by Enrico Ciraci'
January 2024

Test along/track grid generation procedure.

positional arguments:
  input_file            Input file.

options:
  -h, --help            show this help message and exit
  --out_dir OUT_DIR, -O OUT_DIR
                        Output directory.
  --buffer_dist BUFFER_DIST, -B BUFFER_DIST
                        Buffer distance.
  --plot, -P            Plot intermediate results.

Python Dependencies
geopandas: Open source project to make working with geospatial data
    in python easier: https://geopandas.org
pyproj: Python interface to PROJ (cartographic projections and coordinate
    transformations library):
    https://pyproj4.github.io/pyproj/stable/index.html
shapely: Python package for manipulation and analysis of planar geometric
    objects: https://shapely.readthedocs.io/en/stable/
"""
# -  Python Dependencies
from __future__ import print_function
import os
import argparse
import numpy as np
from datetime import datetime
import geopandas as gpd
from shapely.geometry import Polygon
from shapely.affinity import rotate
import matplotlib.pyplot as plt
from iride_csk_frame_grid_utils import (reproject_geodataframe,
                                        rotate_polygon_to_north_up)
from PtsLine import PtsLine, PtsLineIntersect


def main() -> None:
    """
    Test along/track grid generation procedure.
    """
    parser = argparse.ArgumentParser(
        description="""Test along/track grid generation procedure."""
    )
    parser.add_argument('input_file', type=str,
                        help='Input file.')
    # - Output directory - default is current working directory
    parser.add_argument('--out_dir', '-O', type=str,
                        help='Output directory.', default=os.getcwd())
    # - Buffer distance
    parser.add_argument('--buffer_dist', '-B', type=float,
                        help='Buffer distance.', default=2e3)
    # - Number of Cells
    # - Along Track
    parser.add_argument('--az_res', '-R', type=float,
                        help='Cross track grid resolution (m).',
                        default=5e3)
    # - Cross Track Resolution
    parser.add_argument('--n_c', '-C', type=float,
                        help='Number of columns in the grid.',
                        default=3)
    # - Plot Intermediate Results
    parser.add_argument('--plot', '-P', action='store_true',
                        help='Plot intermediate results.')
    # - Parse arguments
    args = parser.parse_args()

    # - set path to input shapefile
    input_shapefile = args.input_file
    #input_shapefile \
    #    = os.path.join('.', 'data', 'csk_frame_map_italy_epsg4326_dissolve',
    #                   'csk_frame_map_italy_epsg4326_dissolve.shp')
    # - set path to output shapefile
    out_dir = args.out_dir
    #out_dir = os.path.join(r'C:\Users\e.ciraci\Desktop\test')
    os.makedirs(out_dir, exist_ok=True)

    # - import input data
    gdf = gpd.read_file(input_shapefile)
    # - get input data crs
    source_crs = gdf.crs.to_epsg()

    # - Number of Cells
    n_c = args.n_c        # - Along Track - Number of Columns
    az_res = args.az_res  # - Cross Track Resolution (km) - Azimuth Resolution

    # - Extract Polygon centroid
    ll_centroid = (gdf['geometry'].centroid.x, gdf['geometry'].centroid.y)
    # - Longitude of the centroid - convert to radians
    lat_cent = ll_centroid[1][0] * np.pi / 180
    # - Estimate an average distortion factor associated to the
    # - usage of Web Mercator Projection (EPSG:3857)
    # - Reference: https://en.wikipedia.org/wiki/Mercator_projection
    d_scale = np.cos(lat_cent)

    # - reproject to  WGS 84 Web Mercator Projection EPSG:3857
    gdf = reproject_geodataframe(gdf, 3857)

    # - remove z coordinate
    d3_coord = gdf['geometry'].loc[0].exterior.coords[:-1]
    d2_coords = Polygon([(coord[0], coord[1]) for coord in d3_coord])

    # - rotate geometries
    rotated_geometry, alpha \
        = rotate_polygon_to_north_up(d2_coords)
    rotated_gdf = gdf.copy()
    rotated_gdf['geometry'] = rotated_geometry

    # - Extract Polygon centroid
    centroid = (rotated_geometry.centroid.x, rotated_geometry.centroid.y)

    # - Points to the left of the centroid
    left_points = [point for point in rotated_geometry.exterior.coords[:-1]
                   if point[0] < centroid[0]]
    # - Points to the right of the centroid
    right_points = [point for point in rotated_geometry.exterior.coords[:-1]
                    if point[0] > centroid[0]]

    # - Find trapezoid corners coordinates
    x_c, y_c = zip(*list(rotated_geometry.exterior.coords))
    x_lpc, y_lpc = zip(*list(left_points))
    x_rpc, y_rpc = zip(*list(right_points))

    # - Corner 1 - Upper Left
    ind_ul = np.argmax(np.array(y_lpc))
    pt_ul = (x_lpc[ind_ul], y_lpc[ind_ul])
    # - Corner 2 - Upper Right
    ind_ur = np.argmax(np.array(y_rpc))
    pt_ur = (x_rpc[ind_ur], y_rpc[ind_ur])
    # - Corner 3 - Lower Right
    ind_lr = np.argmin(np.array(y_rpc))
    pt_lr = (x_rpc[ind_lr], y_rpc[ind_lr])
    # - Corner 4 - Lower Left
    ind_ll = np.argmin(np.array(y_lpc))
    pt_ll = (x_lpc[ind_ll], y_lpc[ind_ll])

    # - Compute trapezoid diagonals equations
    # - Diagonal 1
    ln1 = PtsLine(pt_ul[0], pt_ul[1], pt_lr[0], pt_lr[1])
    # - Diagonal 2
    ln2 = PtsLine(pt_ur[0], pt_ur[1], pt_ll[0], pt_ll[1])

    # - Extend diagonals using a user define buffer
    xs = []
    ys = []
    # - Corner 1 - Upper Left
    x1 = pt_ul[0] - args.buffer_dist
    y1 = ln1.y(x1)
    ul_ext = (x1, y1)
    xs.append(x1)
    ys.append(y1)
    # - Corner 2
    x2 = pt_ur[0] + args.buffer_dist
    y2 = ln2.y(x2)
    ur_ext = (x2, y2)
    xs.append(x2)
    ys.append(y2)
    # - Corner 3
    x3 = pt_lr[0] + args.buffer_dist
    y3 = ln1.y(x3)
    lr_ext = (x3, y3)
    xs.append(x3)
    ys.append(y3)
    # - Corner 4
    x4 = pt_ll[0] - args.buffer_dist
    y4 = ln2.y(x4)
    ll_ext = (x4, y4)
    xs.append(x4)
    ys.append(y4)
    xs.append(x1)
    ys.append(y1)

    # - Trapezoid major axis equation
    ln3 = PtsLine(ul_ext[0], ul_ext[1], ur_ext[0], ur_ext[1])
    # - Trapezoid minor axis equation
    ln4 = PtsLine(ll_ext[0], ll_ext[1], lr_ext[0], lr_ext[1])
    # - Trapezoid left side equation
    ln5 = PtsLine(ul_ext[0], ul_ext[1], ll_ext[0], ll_ext[1])
    # - Trapezoid right side equation
    ln6 = PtsLine(ur_ext[0], ur_ext[1], lr_ext[0], lr_ext[1])

    # - Compute grid number of rows and
    # - Generate coordinates of reference points for the
    # - grid vertical lines
    x_north = np.linspace(ul_ext[0], ur_ext[0], n_c+1)
    x_south = np.linspace(ll_ext[0], lr_ext[0], n_c+1)

    # - Evaluate the y coordinates of the grid vertical lines
    y_north = ln3.y(x_north)
    y_south = ln4.y(x_south)

    # - Compute grid number of rows
    n_r = int(np.ceil(((max(y_north) - min(y_south)) * d_scale) / az_res))

    # - Generate coordinates of reference points for the
    # - grid horizontal lines
    y_vert = np.linspace(min(lr_ext[1], ur_ext[1]),
                         max(ll_ext[1], ul_ext[1]), n_r+1)
    # - Evaluate the x coordinates of the grid horizontal lines
    x_vert_l = []
    x_vert_r = []

    for y in y_vert:
        x_vert_l.append(ln5.x(y))
        x_vert_r.append(ln6.x(y))

    # - Generate list of vertical and horizontal lines
    horiz_lines = [PtsLine(x_vert_l[i], float(y_vert[i]),
                           x_vert_r[i], float(y_vert[i]))
                   for i in range(len(x_vert_l))]
    vert_lines = [PtsLine(float(x_north[i]), float(y_north[i]),
                          float(x_south[i]), float(y_south[i]))
                  for i in range(len(x_north))]

    # - Initialize Grid Corner Matrix
    corners_matrix = []
    for hr in horiz_lines:
        corners_horiz = []
        for vr in vert_lines:
            corners_horiz.append(PtsLineIntersect(hr, vr).intersect())
        corners_matrix.append(corners_horiz)
    # - Convert to numpy array
    corners_matrix = np.array(corners_matrix)
    # - Matrix shape
    n_rows, n_cols, _ = corners_matrix.shape

    # - Compute grid cells corners coordinates & generate output dataframe
    grid_corners = []
    grid_geometry = []
    for i in range(n_rows - 1):
        for j in range(n_cols - 1):
            grid_corners.append([corners_matrix[i, j],
                                 corners_matrix[i, j + 1],
                                 corners_matrix[i + 1, j + 1],
                                 corners_matrix[i + 1, j],
                                 corners_matrix[i, j]])
            grid_geometry.append(rotate(Polygon(grid_corners[-1]), alpha,
                                        origin=centroid))
    # - Create GeoDataFrame and convert to original CRS
    grid_gdf = gpd.GeoDataFrame(geometry=grid_geometry, crs='EPSG:3857')
    grid_gdf = reproject_geodataframe(grid_gdf, source_crs)

    # - Save grid to shapefile
    grid_gdf.to_file(os.path.join(out_dir, output_f_name))

    if args.plot:
        # - Plot rotated geometry
        fig, ax = plt.subplots(figsize=(5, 7))
        ax.set_title('Rotated Geometry')
        ax.set_xlabel('Easting')
        ax.set_ylabel('Northing')
        ax.scatter(x_c, y_c, color='blue', zorder=0)
        ax.scatter(pt_ul[0], pt_ul[1], color='yellow')
        ax.scatter(pt_ur[0], pt_ur[1], color='yellow')
        ax.scatter(pt_lr[0], pt_lr[1], color='yellow')
        ax.scatter(pt_ll[0], pt_ll[1], color='yellow')
        ax.scatter(ul_ext[0], ul_ext[1], color='red')
        ax.scatter(ur_ext[0], ur_ext[1], color='red')
        ax.scatter(lr_ext[0], lr_ext[1], color='red')
        ax.scatter(ll_ext[0], ll_ext[1], color='red')
        ax.scatter(xs, ys, color='orange', marker='x')
        ax.plot([pt_ul[0], pt_lr[0]], [pt_ul[1], pt_lr[1]], color='cyan')
        ax.scatter(x_north, y_north, color='green')
        ax.scatter(x_south, y_south, color='green')
        ax.scatter(x_vert_l, y_vert, color='green')
        ax.scatter(x_vert_r, y_vert, color='green')
        ax.plot(*zip(*grid_corners[6]), color='magenta')
        ax.grid()
        plt.show()
        plt.close()


# - run main program
if __name__ == '__main__':
    start_time = datetime.now()
    main()
    end_time = datetime.now()
    print(f"# - Computation Time: {end_time - start_time}")
