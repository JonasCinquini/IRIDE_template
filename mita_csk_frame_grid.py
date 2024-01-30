u"""
Written by Jonas Cinquini
January 2024

Process a shapefile, create grids within polygons, and save the result
to separate shapefiles.

Python Dependencies
geopandas: Open source project to make working with geospatial data
    in python easier: https://geopandas.org
"""

import os
import geopandas as gpd
from mita_csk_frame_grid_utils import (reproject_geodataframe,
                                       create_grid_within_polygon,
                                       add_frame_code_field)


def grid_from_area(input_shapefile: str, output_folder: str,
                   buffer_dist: float = None, x_frame_split: int = 3,
                   y_frame_split: int = 6, dissolve: bool = False) \
        -> list[str]:
    """
    Process a shapefile, create grids within polygons, and save the result
    to separate shapefiles.

    Parameters:
        input_shapefile (str): Path to the input shapefile.
        output_folder (str): Path to the output folder where separate grid
            shapefiles will be saved.
        buffer_dist (float, optional): Buffer distance for the input polygons.
        x_frame_split (int, optional): Number of columns in the grid.
        y_frame_split (int, optional): Number of rows in the grid.
        dissolve (bool, optional): Whether to dissolve the polygons
        in the input shapefile.

    Returns:
        output_files (list): List of paths to the saved output shapefiles.
    """
    # Read the input shapefile
    gdf = gpd.read_file(input_shapefile)
    orig_epsg = gdf.crs.to_epsg()

    # Reproject to EPSG:3857
    gdf = reproject_geodataframe(gdf, 3857)

    # Apply buffer if specified
    if buffer_dist:
        buffered_polygons = gdf.geometry.buffer(buffer_dist,
                                                cap_style=3, join_style=2)
        gdf = gpd.GeoDataFrame(geometry=buffered_polygons, crs=gdf.crs)

    output_files = []

    # Check if dissolve is needed
    if dissolve and len(gdf['geometry']) > 1:
        dissolved_geometry = gdf.unary_union
        # Get the centroid of non-rotated dissolved geometries
        centroid = (dissolved_geometry.centroid.x,
                    dissolved_geometry.centroid.y)
        # Generates the fishnet grid of input frame polygons
        grid_gdf = create_grid_within_polygon(dissolved_geometry,
                                              x_frame_split, y_frame_split)
        # Reproject to the original coordinate
        grid_gdf = reproject_geodataframe(grid_gdf, orig_epsg)
        grid_gdf = add_frame_code_field(grid_gdf)
        output_file = os.path.join(output_folder, f'grid_dissolved.shp')
        grid_gdf.to_file(output_file)
        output_files.append(output_file)
    else:
        # Process each polygon in the GeoDataFrame
        for idx, geometry in enumerate(gdf['geometry']):
            grid_gdf = create_grid_within_polygon(geometry,
                                                  x_frame_split, y_frame_split)
            # reproject to the original coordinate reference system
            grid_gdf = reproject_geodataframe(grid_gdf, orig_epsg)
            grid_gdf = add_frame_code_field(grid_gdf)
            # Save the grid to a new shapefile
            output_file = os.path.join(output_folder, f'grid_{idx + 1}.shp')
            grid_gdf.to_file(output_file)
            output_files.append(output_file)
    
    return output_files
