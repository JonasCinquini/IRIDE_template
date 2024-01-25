#!/usr/bin/env python
u"""
Written by Enrico Ciraci'
January 2024

Generate a regular grid along each of COSMO-SkyMed tracks
from the MapItaly project.

See generate_grid.py for more details about the grid generation algorithm.

usage: mapitaly_at_grid.py [-h] [--out_dir OUT_DIR] [--buffer_dist BUFFER_DIST]
    [--az_res AZ_RES] [--n_c N_C] [--plot] input_file

Generate a regular grid along each of COSMO-SkyMed tracks from
the MapItaly project.

positional arguments:
  input_file            Input file.

options:
  -h, --help            show this help message and exit
  --out_dir OUT_DIR, -O OUT_DIR
                        Output directory.
  --buffer_dist BUFFER_DIST, -B BUFFER_DIST
                        Buffer distance.
  --az_res AZ_RES, -R AZ_RES
                        Cross track grid resolution (m) [def. 5e3m].
  --n_c N_C, -C N_C     Number of columns in the grid.
  --plot, -P            Save Map Showing the generated grid.



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
cartopy: Python package designed for geospatial data processing in order to
    produce maps and other geospatial data analyses:
    https://scitools.org.uk/cartopy/docs/latest/

"""
# -  Python Dependencies
from __future__ import print_function
import os
import argparse
from datetime import datetime
from tqdm import tqdm
import geopandas as gpd
from matplotlib import pyplot as plt
import cartopy.crs as ccrs
# - Custom Dependencies
from generate_grid import generate_grid
from rm_z_coord import rm_z_coord


def main() -> None:
    """
    Generate a regular grid along each of COSMO-SkyMed tracks
    from the MapItaly project.
    """
    parser = argparse.ArgumentParser(
        description="""Generate a regular grid along each of COSMO-SkyMed 
        tracks from the MapItaly project."""
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
                        help='Cross track grid resolution (m) [def. 5e3m].',
                        default=5e3)
    # - Cross Track Resolution
    parser.add_argument('--n_c', '-C', type=float,
                        help='Number of columns in the grid.',
                        default=3)
    # - Plot Intermediate Results
    parser.add_argument('--plot', '-P', action='store_true',
                        help='Save Map Showing the generated grid.')
    # - Parse arguments
    args = parser.parse_args()

    # - Number of Cells
    n_c = args.n_c        # - Along Track - Number of Columns
    az_res = args.az_res  # - Cross Track Resolution (km) - Azimuth Resolution
    buffer_dist = args.buffer_dist  # - Buffer distance

    # - Path to data
    dat_path = args.input_file
    # - Create output directory
    out_dir = args.out_dir
    os.makedirs(out_dir, exist_ok=True)

    # - Read data
    gdf = gpd.read_file(dat_path)
    print(f"# - Input GeoDataframe: {dat_path}")
    print(f"# - GeoDataframe shape: {gdf.shape}")

    # - Remove Z-Coordinate from geometry
    gdf = rm_z_coord(gdf)

    # - Extract 'Path' column unique values
    path_list = gdf['Path'].unique().tolist()
    # - Loop through the GeoDataFrame lines and extract a reference grid
    # # - for each sub-track.
    for p in tqdm(path_list, desc='# - Processing Asc and Des tracks:',
                  ncols=100):
        # - Extract data relative to a certain sub-track
        p_gdf = gdf[gdf['Path'] == p].reset_index(drop=True)
        gdf_grid = generate_grid(p_gdf, n_c=n_c,
                                 az_res=az_res,
                                 buffer_dist=buffer_dist)

        # - Extract track acquisition parameters
        # - Beam [Sensor Mode] [Pass] [Satellite]
        s_mode = p_gdf['SensorMode'].unique().tolist()[0]
        # - Geometry
        pass_geom = p_gdf['Pass'].unique().tolist()[0]
        if pass_geom == 'ASCENDING':
            pass_geom = 'ASC'
        else:
            pass_geom = 'DES'
        # - Satellite
        sat = p_gdf['Satellite'].unique().tolist()[0]
        if sat == 'COSMO-SkyMed-1':
            sat_short = 'CSK1'
        elif sat == 'COSMO-SkyMed-2':
            sat_short = 'CSK2'
        elif sat == 'COSMO-SkyMed-SG-1':
            sat_short = 'CSG1'
        elif sat == 'COSMO-SkyMed-SG-2':
            sat_short = 'CSG2'
        else:
            sat_short = 'CSM'   # - Match for Satellite Name not found.
        out_name = f"grid_{sat_short}_{p}_{s_mode}_{pass_geom}.shp"

        # - Save grid to file
        out_path = os.path.join(out_dir, out_name)
        gdf_grid.to_file(out_path)

        if args.plot:
            plt.figure(figsize=(5, 5.2))
            extent = [5, 20, 36, 48]
            ax = plt.axes(projection=ccrs.PlateCarree())
            ax.coastlines()
            gdf_grid.plot(ax=ax, linewidth=0.2,
                          facecolor="none", edgecolor="b", zorder=2)
            p_gdf.plot(ax=ax, linewidth=0.1,
                       facecolor="r", edgecolor="r", zorder=1, alpha=0.5)
            ax.set_extent(extent)
            gl = ax.gridlines(draw_labels=True)
            gl.top_labels = False
            gl.right_labels = False
            ax.set_title(f"{sat} - {p} - {s_mode} - {pass_geom}")
            plt.savefig(os.path.join(out_dir, f"{out_name}"
                                     .replace(".shp", ".png")),
                        dpi=300, bbox_inches='tight')
            plt.close()


# - run main program
if __name__ == '__main__':
    start_time = datetime.now()
    main()
    end_time = datetime.now()
    print(f"# - Computation Time: {end_time - start_time}")
