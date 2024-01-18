import os
import math
import pandas as pd
import geopandas as gpd
from osgeo import ogr
from math import ceil
from shapely.geometry import Polygon
from shapely.affinity import rotate


def get_fishnet_grid(xmin, ymin, xmax, ymax, gridWidth, gridHeight):
    # Get range
    rows = ceil((ymax - ymin) / gridHeight)
    # Get azimuth
    cols = ceil((xmax - xmin) / gridWidth)

    polygons = []

    for i in range(cols):
        for j in range(rows):
            # Coordinates of the grid cell
            left = xmin + i * gridWidth
            right = left + gridWidth
            top = ymax - j * gridHeight
            bottom = top - gridHeight

            # Create polygon geometry
            polygon = Polygon([(left, top), (right, top), (right, bottom), (left, bottom), (left, top)])
            polygons.append(polygon)

    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame(geometry=polygons, crs='EPSG:3857')

    return gdf



def get_frame_grid(input_frame_shp, grid_output_shp, buffer_dist=None, x_frame_split=3, y_frame_split=6):
    # Step 1: Read the polygon shapefile
    gdf = gpd.read_file(input_frame_shp)
    orig_crs = gdf.crs

    # Step 2: Convert to EPSG:3857
    gdf = gdf.to_crs(epsg=3857)

    # Step 3: If required generates a buffer of the polygon 
    if buffer_dist:
        buffered_polygons = gdf.geometry.buffer(buffer_dist, cap_style=3, join_style=2)
        gdf = gpd.GeoDataFrame(geometry=buffered_polygons, crs=gdf.crs)
    # Step 4: Iterate through each geometry
    grid_gdf_list = []
    for idx, geometry in enumerate(gdf['geometry']):
        # Step 5: Get the tilt angle of the boundary polygon
        # Calculate the angle between one of the sides of the rectangle and the x-axis.
        rectangle = geometry
        p1, p2 = rectangle.exterior.coords[0], rectangle.exterior.coords[1]
        angle = math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0]))

        # Step 6: Rotate the boundary polygon to be north up
        centroid = (geometry.centroid.x, geometry.centroid.y)
        rotated_geometry = rotate(geometry, -angle, origin=centroid)

        # Step 7: Get extent coordinates
        ##QUA INVECE USARE .BOUNDS ESTRARRE XMIN XMAX... DA EXTERIOR COORDS##
        min_x, min_y, max_x, max_y = rotated_geometry.bounds

        # Step 8: Create a grid inside the polygon boundary

        #xmin, ymin, xmax, ymax = min_x, min_y + 4700, max_x, max_y
        xmin, ymin, xmax, ymax = float(min_x), float(min_y), float(max_x), float(max_y)
        x_spacing = (xmax-xmin)/x_frame_split
        y_spacing = (ymax-ymin)/y_frame_split
        grid_gdf = get_fishnet_grid(xmin, ymin, xmax, ymax, gridWidth=x_spacing,gridHeight=y_spacing)

        # Step 9: Rotate back and reproject the grid with the original tilt and coordinate reference system
		
        rotated_geometries = [rotate(geometry, angle, origin=centroid) for geometry in grid_gdf['geometry']]
        grid_gdf['geometry'] = rotated_geometries

#        # Step 10: Shift the grid polygons to the center of the original frame polygon
#        grid_gdf_dissolve = grid_gdf.dissolve()
#        grid_centroid = (grid_gdf_dissolve["geometry"].centroid.x, grid_gdf_dissolve["geometry"].centroid.y)
#        centroid_x_offset = centroid[0] - grid_centroid[0]
#        centroid_y_offset = centroid[1] - grid_centroid[1]
#        grid_gdf = grid_gdf.translate(xoff=float(centroid_x_offset), yoff=float(centroid_y_offset))

        # Append to the list
        grid_gdf_list.append(grid_gdf)

    # Combine all grid GeoDataFrames
    final_grid_gdf = gpd.GeoDataFrame(pd.concat(grid_gdf_list, ignore_index=True), crs=gdf.crs)
#    final_grid_gdf = gpd.GeoDataFrame(geometry=pd.concat(grid_gdf_list), crs=gdf.crs)
#    final_grid_gdf = grid_gdf

    # Step 11: Export the grid to shapefile
    final_grid_gdf.to_file(grid_output_shp)