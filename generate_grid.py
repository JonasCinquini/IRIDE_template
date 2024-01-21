#!/usr/bin/env python
u"""
Written by Enrico Ciraci'
January 2024

Compute a regular grid along the provided satellite track.

    1. Merge frames polygons into a single track polygon.
    2. Compute the centroid of the track polygon.
    3. Project the track polygon to 3857 Web Mercator Projection.
    4. Rotate the track polygon to align it with the North-South direction.
    5. Compute the trapezoid corners coordinates.
    6. Compute the trapezoid diagonals equations.
    7. Extend diagonals using a user define buffer.
    8. Split the vertical and horizontal dimensions into a number of segments
       defined by az_res and n_c parameters.
    9. Compute the grid cells corners coordinates.
    10. Generate output shapefile.

positional arguments:
  input_file            Input file.

options:
  -h, --help            show this help message and exit
  --out_dir OUT_DIR, -O OUT_DIR
                        Output directory.
  --buffer_dist BUFFER_DIST, -B BUFFER_DIST
                        Buffer distance.
  --az_res AZ_RES, -R AZ_RES
                        Cross track grid resolution (m).
  --n_c N_C, -C N_C     Number of columns in the grid.
  --plot, -P            Plot intermediate results.


Python Dependencies
geopandas: Open source project to make working with geospatial data
    in python easier: https://geopandas.org
pyproj: Python interface to PROJ (cartographic projections and coordinate
    transformations library):
    https://pyproj4.github.io/pyproj/stable/index.html
shapely: Python package for manipulation and analy_sis of planar geometric
    objects: https://shapely.readthedocs.io/en/stable/
matplotlib: Comprehensive library for creating static, animated, and
    interactive visualizations in Python:
    https://matplotlib.org

"""
# -  Python Dependencies
from __future__ import print_function
import os
import argparse
from datetime import datetime
import numpy as np
import geopandas as gpd
from shapely.geometry import Polygon, Point
from shapely.affinity import rotate
from pyproj import CRS, Transformer
from shapely.ops import transform
import matplotlib.pyplot as plt
from iride_csk_frame_grid_utils import (reproject_geodataframe,
                                        rotate_polygon_to_north_up)
from PtsLine import PtsLine, PtsLineIntersect


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

    # - Number of Cells
    n_c = args.n_c        # - Along Track - Number of Columns
    az_res = args.az_res  # - Cross Track Resolution (km) - Azimuth Resolution

    # - set path to input shapefile
    input_shapefile = args.input_file
    output_f_name \
        = os.path.basename(input_shapefile).replace('.shp','_grid.shp')
    # - set path to output shapefile
    out_dir = args.out_dir
    os.makedirs(out_dir, exist_ok=True)

    # - import input data
    gdf = gpd.read_file(input_shapefile)
    # - get input data crs
    source_crs = gdf.crs.to_epsg()
    # - extract only needed columns
    gdf = gdf[['geometry']]

    # - remove z coordinate
    no_z_coord = []
    for _, row in gdf.iterrows():
        # - remove z coordinate
        z_coords = row['geometry'].exterior.coords[:-1]
        no_z_coord.append(Polygon([(crd[0], crd[1]) for crd in z_coords]))
    gdf['geometry'] = no_z_coord

    # - Merge frames polygons into a single track polygon
    gdf_t \
        = (gpd.GeoDataFrame(geometry=[gdf.unary_union], crs=source_crs)
           .explode(index_parts=False).reset_index(drop=True))

    # - Compute Track Centroid - Need to reproject the track geometry
    # - to minimize distortion in the calculation.
    # - 1. Project to  WGS 84 Web Mercator Projection EPSG:3857
    # - 2. Compute Centroid
    r_geom \
        = reproject_geometry(gdf_t['geometry'],
                             source_crs, 3857).loc[0]
    proj_centroid = Point(r_geom.centroid.x, r_geom.centroid.y)
    ll_centroid = reproject_geometry(proj_centroid, 3857, source_crs)

    # - Longitude of the centroid - convert to radians
    lat_cent = ll_centroid.y * np.pi / 180
    # - Estimate an average distortion factor associated to the
    # - usage of Web Mercator Projection (EPSG:3857)
    # - Reference: https://en.wikipedia.org/wiki/Mercator_projection
    d_scale = np.cos(lat_cent)

    # - reproject to  WGS 84 Web Mercator Projection EPSG:3857
    gdf = reproject_geodataframe(gdf_t, 3857)

    # - If still present remove z coordinate
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
    ln_1 = PtsLine(pt_ul[0], pt_ul[1], pt_lr[0], pt_lr[1])
    # - Diagonal 2
    ln_2 = PtsLine(pt_ur[0], pt_ur[1], pt_ll[0], pt_ll[1])

    # - Extend diagonals using a user define buffer
    x_s = []
    y_s = []
    # - Corner 1 - Upper Left
    x_1 = pt_ul[0] - args.buffer_dist
    y_1 = ln_1.y_val(x_1)
    ul_ext = (x_1, y_1)
    x_s.append(x_1)
    y_s.append(y_1)
    # - Corner 2
    x_2 = pt_ur[0] + args.buffer_dist
    y_2 = ln_2.y_val(x_2)
    ur_ext = (x_2, y_2)
    x_s.append(x_2)
    y_s.append(y_2)
    # - Corner 3
    x_3 = pt_lr[0] + args.buffer_dist
    y_3 = ln_1.y_val(x_3)
    lr_ext = (x_3, y_3)
    x_s.append(x_3)
    y_s.append(y_3)
    # - Corner 4
    x_4 = pt_ll[0] - args.buffer_dist
    y_4 = ln_2.y_val(x_4)
    ll_ext = (x_4, y_4)
    x_s.append(x_4)
    y_s.append(y_4)
    x_s.append(x_1)
    y_s.append(y_1)

    # - Trapezoid major axis equation
    ln_3 = PtsLine(ul_ext[0], ul_ext[1], ur_ext[0], ur_ext[1])
    # - Trapezoid minor axis equation
    ln_4 = PtsLine(ll_ext[0], ll_ext[1], lr_ext[0], lr_ext[1])
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
    y_north = ln_3.y_val(x_north)
    y_south = ln_4.y_val(x_south)

    # - Compute grid number of rows
    n_r = int(np.ceil(((max(y_north) - min(y_south)) * d_scale) / az_res))

    # - Generate coordinates of reference points for the
    # - grid horizontal lines
    y_vert = np.linspace(min(lr_ext[1], ur_ext[1]),
                         max(ll_ext[1], ul_ext[1]), n_r+1)
    # - Evaluate the x coordinates of the grid horizontal lines
    x_vert_l = []
    x_vert_r = []

    for y_p in y_vert:
        x_vert_l.append(ln5.x_val(y_p))
        x_vert_r.append(ln6.x_val(y_p))

    # - Generate list of vertical and horizontal lines
    horiz_lines = [PtsLine(x_vert_l[i], float(y_vert[i]),
                           x_vert_r[i], float(y_vert[i]))
                   for i in range(len(x_vert_l))]
    vert_lines = [PtsLine(float(x_north[i]), float(y_north[i]),
                          float(x_south[i]), float(y_south[i]))
                  for i in range(len(x_north))]

    # - Initialize Grid Corner Matrix
    corners_matrix = []
    for h_r in horiz_lines:
        corners_horiz = []
        for v_r in vert_lines:
            corners_horiz.append(PtsLineIntersect(h_r, v_r).intersection)
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
        _, ax = plt.subplots(figsize=(5, 7))
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
        ax.scatter(x_s, y_s, color='orange', marker='x')
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
