#!/usr/bin/env python
"""
Written by Enrico Ciraci'
Use a Spatial Join to distribute the PS points available within
the boundaries of a CSK frame over the relative along-track grid.
"""
import os
from datetime import datetime
import geopandas as gpd
import matplotlib.pyplot as plt


def main() -> None:
    """
    Use a Spatial Join to distribute the PS points available within
    the boundaries of a CSK frame over the relative along-track grid.
    """
    # - import sample data
    smp_input \
        = os.path.join('.', 'data', 'shapefiles',
                       'csk_ps_sample_Nocera_Terinese_A_epsg4326.shp')

    # - read sample data
    gdf_smp = gpd.read_file(smp_input)

    # - Import CSK Along Track Grid
    csk_at_grid \
        = os.path.join('.', 'data', 'shapefiles',
                       'grid_CSG2_151_STR-007_ASC.shp')
    gdf_csk = gpd.read_file(csk_at_grid)

    # - Compute spatial join between set of points and grid
    gdf_smp = gpd.sjoin(gdf_smp, gdf_csk, how="inner", op="within")

    # - Show results of the spatial join
    fig, ax = plt.subplots()
    gdf_smp.plot(ax=ax, c=gdf_smp['row'], cmap='viridis', legend=True)
    plt.show()


# - run main program
if __name__ == '__main__':
    start_time = datetime.now()
    main()
    end_time = datetime.now()
    print(f"# - Computation Time: {end_time - start_time}")
