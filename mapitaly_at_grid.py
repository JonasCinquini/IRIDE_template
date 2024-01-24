# -  Python Dependencies
from __future__ import print_function
import os
import argparse
from datetime import datetime
import numpy as np
import geopandas as gpd
from rm_z_coord import rm_z_coord


def main() -> None:
    # - Path to data
    dat_path = os.path.join(os.path.expanduser("~"), 'Desktop', 'MapItaly',
                            'MAPITALY_CSG1_2_CSK1_2.shp')

    # - Read data
    gdf = gpd.read_file(dat_path)
    print(f"# - Data loaded: {dat_path}")
    print(f"# - Data shape: {gdf.shape}")
    print(f"# - Data columns: {gdf.columns}")

    # - Remove Z-Coordinate from geometry
    gdf = rm_z_coord(gdf)

    # - Loop through the GeoDataFrame lines and extract a reference grid
    # - for each sub-track.
    for _, row in gdf.iterrows():
        # - Check Polygon Validity
        print(row['geometry'].is_valid)




# - run main program
if __name__ == '__main__':
    start_time = datetime.now()
    main()
    end_time = datetime.now()
    print(f"# - Computation Time: {end_time - start_time}")
