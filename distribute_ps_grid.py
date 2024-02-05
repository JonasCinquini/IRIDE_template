#!/usr/bin/env python
"""
Written by Enrico Ciraci'
Use a Spatial Join to distribute the PS points available within
the boundaries of a CSK frame over the relative along-track grid.

usage: distribute_ps_grid.py [-h] [--out_dir OUT_DIR]
    [--out_format {parquet,shp}] [--plot] input_file grid_file

Distribute PS points over the CSK grid

positional arguments:
  input_file            Input file.
  grid_file             CSK Along Track Grid file.

options:
  -h, --help            show this help message and exit
  --out_dir OUT_DIR, -O OUT_DIR
                        Output directory.
  --out_format {parquet,shp}, -F {parquet,shp}
                        Output file format.
  --plot, -P            Plot the results showing the PS partition.

Python Dependencies
geopandas: Open source project to make working with geospatial data
    in python easier: https://geopandas.org
dask-geopandas: Distributed geospatial operations using Dask:
    https://dask-geopandas.readthedocs.io
matplotlib: Comprehensive library for creating static, animated, and
    interactive visualizations in Python: https://matplotlib.org
"""
import os
import argparse
from datetime import datetime
import geopandas as gpd
import dask_geopandas as dgpd
import matplotlib.pyplot as plt


def distribute_ps_grid(input_file: str, grid_file: str) -> gpd.GeoDataFrame:
    """
    Use a Spatial Join to distribute the PS points available within
    Args:
        input_file: Absolute Path to the input file.
        grid_file: Absolute Path to the grid file.
    Returns: None
    """
    if not os.path.isfile(input_file):
        raise FileNotFoundError(f"File not found: {input_file}")
    # - Import PS Sample Data
    gdf_smp = dgpd.read_file(input_file, npartitions=4)

    # - Import CSK AlongTrack Grid
    if not os.path.isfile(grid_file):
        raise FileNotFoundError(f"File not found: {grid_file}")
    gdf_csk = gpd.read_file(grid_file)

    # - Print input/output file names
    print(f"# - Input PS Sample: {input_file}")
    print(f"# - Input CSK Grid: {grid_file}")
    print("# - Compute Spatial Join between PS Sample and CSK Grid.")

    # - Compute spatial join between set of points and grid
    gdf_smp = gdf_smp.sjoin(gdf_csk, how="inner", predicate="within")

    return gdf_smp


def main() -> None:
    """
    Use a Spatial Join to distribute the PS points available within
    the boundaries of a CSK frame over the relative along-track grid.
    """
    # - Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Distribute PS points over the CSK grid"
    )
    # - Input file
    parser.add_argument('input_file', type=str,
                        help='Input file.')
    # - Input CSK AT Grid file
    parser.add_argument('grid_file', type=str,
                        help='CSK Along Track Grid file.')
    # - Output directory - default is current working directory
    parser.add_argument('--out_dir', '-O', type=str,
                        help='Output directory.', default=os.getcwd())
    # - Output file format
    parser.add_argument('--out_format', '-F', type=str,
                        help='Output file format.', default='parquet',
                        choices=['parquet', 'shp'])
    # - Plot Intermediate Results
    parser.add_argument('--plot', '-P', action='store_true',
                        help='Plot the results showing the PS partition.')
    args = parser.parse_args()

    # - import sample data
    smp_input = args.input_file

    # - Import CSK Along Track Grid
    csk_at_grid = args.grid_file

    # - Distribute PS points over the CSK grid
    gdf_smp = distribute_ps_grid(smp_input, csk_at_grid
                                 )
    # - Drop unnecessary columns
    print("# - Drop unnecessary columns & Convert Dask-GeoDataFrame "
          "to GeoDataFrame.")
    gdf_smp = gdf_smp.drop(columns=['index_right', 'type', 'rand_point',
                                    'index', 'name',  'csm_path'])
    gdf_smp = gdf_smp.reset_index(drop=True)
    gdf_smp = gdf_smp.compute()

    # - Save the results
    print("# - Save the results.")
    out_dir = args.out_dir
    os.makedirs(out_dir, exist_ok=True)
    out_file \
        = os.path.join(out_dir, os.path.basename(smp_input)
                       .replace('.shp', f'_rc.{args.out_format}'))

    if args.out_format == 'shp':
        gdf_smp.to_file(out_file)
    else:
        if os.path.isfile(out_file):
            os.remove(out_file)
        gdf_smp.to_parquet(out_file)

    if args.plot:
        # - Plot the results
        fig, ax = plt.subplots()
        gdf_smp.plot(ax=ax, c=gdf_smp['row'], cmap='viridis', legend=True)
        plt.show()


# - run main program
if __name__ == '__main__':
    start_time = datetime.now()
    main()
    end_time = datetime.now()
    print(f"# - Computation Time: {end_time - start_time}")
