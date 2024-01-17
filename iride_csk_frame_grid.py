import math
import pandas as pd
import numpy as np
import geopandas as gpd
from osgeo import ogr
from shapely.geometry import Polygon
from shapely.geometry import MultiPolygon
from shapely.affinity import rotate



import os, sys
from osgeo import ogr
from math import ceil

##UNDER CONSTRUCTION##
#def fishnet_grid(out_polygon_wkt, ulx=1201773.8807996798, uly=5836508.814290593, lrx=1260860.5711285786, lry=5773457.291196505, x_spacing=19695.56344296628, y_spacing=10000):
#
#    dx = x_spacing/2
#    dy = y_spacing/2
#    xx, yy = np.meshgrid(np.arange(ulx-dx, lrx+dx, x_spacing),np.arange(lry-dy, uly-dy, y_spacing),)
#    #drv = ogr.GetDriverByName('ESRI Shapefile')
#    #dest_srs = ogr.osr.SpatialReference()
#    #dest_srs.ImportFromEPSG(3857)
#    #ds = drv.CreateDataSource(output_shapefile)
#    #lyr = ds.CreateLayer(output_shapefile, dest_srs, geom_type=ogr.wkbPolygon)
#    #fdefn = lyr.GetLayerDefn()
#    for x,y in zip(xx.ravel(), yy.ravel()):
#        out_polygon_wkt = f" POLYGON (({x+dx} {y+dy},{x-dx} {y+dy}, {x-dx} {y-dy}, {x+dx} {y-dy}, {x+dx} {y+dy}))"
#        #ft = ogr.Feature(fdefn)
#        #ft.SetGeometry(ogr.CreateGeometryFromWkt(poly_wkt))
#        #lyr.CreateFeature(ft)
#        #ft = None
#    #lyr = None
#    #ds = None
##UNDER CONSTRUCTION

def get_frame_grid(input_frame_shp, grid_output_shp, buffer_dist=2000, x_frame_split=3, y_spacing=10000):
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
        min_x, min_y, max_x, max_y = rotated_geometry.bounds
        
        # Step 8: Create a grid inside the polygon boundary
        if buffer_dist:
            xmin, ymin, xmax, ymax = min_x, min_y + (buffer_dist + 4700), max_x, max_y
        else:
            #xmin, ymin, xmax, ymax = min_x, min_y + 4700, max_x, max_y
            xmin, ymin, xmax, ymax = min_x, min_y, max_x, max_y
        x_spacing = (xmax-xmin)/x_frame_split
        # Create a grid of polygons
        
        grid_polygons = []
        for x in range(int(xmin), int((xmax)-int(x_spacing)), int(x_spacing)):
            for y in range(int(ymin), int((ymax)-int(y_spacing)), int(y_spacing)):
                grid_square = Polygon([(x, y), (x + x_spacing, y), (x + x_spacing, y + y_spacing), (x, y + y_spacing)])
                grid_polygons.append(grid_square)

        # Create a GeoDataFrame from the grid polygons
        grid_gdf = gpd.GeoDataFrame(geometry=grid_polygons, crs=gdf.crs)
        
        # Step 9: Rotate back and reproject the grid with the original tilt and coordinate reference system
        rotated_geometries = [rotate(geometry, angle, origin=centroid) for geometry in grid_gdf['geometry']]
        grid_gdf['geometry'] = rotated_geometries

        # Step 10: Shift the grid polygons to the center of the original frame polygon
        grid_gdf_dissolve = grid_gdf.dissolve()
        grid_centroid = (grid_gdf_dissolve["geometry"].centroid.x, grid_gdf_dissolve["geometry"].centroid.y)
        centroid_x_offset = centroid[0] - grid_centroid[0]
        centroid_y_offset = centroid[1] - grid_centroid[1]
        grid_gdf = grid_gdf.translate(xoff=float(centroid_x_offset), yoff=float(centroid_y_offset))
#        grid_gdf = grid_gdf.translate(xoff=centroid_x_offset, yoff=centroid_y_offset)

        # Append to the list
        grid_gdf_list.append(grid_gdf)

    # Combine all grid GeoDataFrames
    final_grid_gdf = gpd.GeoDataFrame(geometry=pd.concat(grid_gdf_list), crs=gdf.crs)
    
    # Step 11: Export the grid to shapefile
    final_grid_gdf.to_file(grid_output_shp)


def OBSOLETE_2_get_frame_grid(input_frame_shp, grid_output_shp, buffer_dist=2000, x_spacing=25000, y_spacing=10000):
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
        min_x, min_y, max_x, max_y = rotated_geometry.bounds
        
        # Step 8: Create a grid inside the polygon boundary
        if buffer_dist:
            xmin, ymin, xmax, ymax = min_x, min_y + (buffer_dist + 4700), max_x, max_y
        else:
            #xmin, ymin, xmax, ymax = min_x, min_y + 4700, max_x, max_y
            xmin, ymin, xmax, ymax = min_x, min_y, max_x, max_y
        
        # Create a grid of polygons
        grid_polygons = []
        for x in range(int(xmin), int(xmax), int(x_spacing)):
            for y in range(int(ymin), int(ymax), int(y_spacing)):
                grid_square = Polygon([(x, y), (x + x_spacing, y), (x + x_spacing, y + y_spacing), (x, y + y_spacing)])
                grid_polygons.append(grid_square)

        # Create a GeoDataFrame from the grid polygons
        grid_gdf = gpd.GeoDataFrame(geometry=grid_polygons, crs=gdf.crs)
        
        # Step 9: Rotate back and reproject the grid with the original tilt and coordinate reference system
        rotated_geometries = [rotate(geometry, angle, origin=centroid) for geometry in grid_gdf['geometry']]
        grid_gdf['geometry'] = rotated_geometries

        # Step 10: Shift the grid polygons to the center of the original frame polygon
        grid_gdf_dissolve = grid_gdf.dissolve()
        grid_centroid = (grid_gdf_dissolve["geometry"].centroid.x, grid_gdf_dissolve["geometry"].centroid.y)
        centroid_x_offset = centroid[0] - grid_centroid[0]
        centroid_y_offset = centroid[1] - grid_centroid[1]
		grid_gdf = grid_gdf.translate(xoff=float(centroid_x_offset), yoff=float(centroid_y_offset))
#        grid_gdf = grid_gdf.translate(xoff=centroid_x_offset, yoff=centroid_y_offset)

        # Append to the list
        grid_gdf_list.append(grid_gdf)

    # Combine all grid GeoDataFrames
    final_grid_gdf = gpd.GeoDataFrame(geometry=pd.concat(grid_gdf_list), crs=gdf.crs)
    
    # Step 11: Export the grid to shapefile
    final_grid_gdf.to_file(grid_output_shp)







####SINGLE FRAME INPUT VERSION####
def OBSOLETE_get_frame_grid(input_frame_shp, grid_output_shp, buffer_dist=2000, x_spacing=25000, y_spacing=10000):
    # Step 1: Read the polygon shapefile
    gdf = gpd.read_file(input_frame_shp)
    orig_crs = gdf.crs
    
    # Step 2: Convert to EPSG:3857
    gdf = gdf.to_crs(epsg=3857)

    # Step 3: If required generates a buffer of the polygon 
    if buffer_dist:
        buffered_polygon = gdf.geometry.buffer(buffer_dist, cap_style=3, join_style=2)
        gdf = gpd.GeoDataFrame(geometry=buffered_polygon, crs=gdf.crs)
    
    # Step 4: Get the tilt angle of the boundary polygon
    # Calculate the angle between one of the sides of the rectangle and the x-axis.
    
    # Assuming the rectangle is a Polygon
    rectangle = gdf.geometry.iloc[0]
    
    # Get the coordinates of two points on one side of the rectangle
    p1, p2 = rectangle.exterior.coords[0], rectangle.exterior.coords[1]
    
    # Calculate the angle between the line formed by p1 and p2 and the x-axis
    angle = math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0]))
    
    # Step 5: Rotate the boundary polygon to be north up
    # Assuming 'angle' is the tilt angle, you can rotate the polygon using Shapely's affinity module
    centroid = (gdf["geometry"].centroid.x,gdf["geometry"].centroid.y)
    gdf['geometry'] = gdf['geometry'].rotate(-angle, origin=centroid)
    
    # Step 6: Get extent coordinates
    min_x, min_y, max_x, max_y = gdf.geometry.total_bounds
    
    # Step 7: Create a grid (5000x5000m) inside the polygon boundary
#    grid_size = 5000
    if buffer_dist:
        xmin, ymin, xmax, ymax = min_x, min_y+(buffer_dist+4700), max_x, max_y # 4700 = half of frame overlaps in y
    else: xmin, ymin, xmax, ymax = min_x, min_y+(4700), max_x, max_y
    
    # Create a grid of polygons
    grid_polygons = []
    for x in range(int(xmin), int(xmax), int(x_spacing)):
        for y in range(int(ymin), int(ymax), int(y_spacing)):
            grid_square = Polygon([(x, y), (x + x_spacing, y), (x + x_spacing, y + y_spacing), (x, y + y_spacing)])
            grid_polygons.append(grid_square)
    # To clip the grid only where it intersects the frame polygon
#            if grid_square.intersects(gdf.geometry.iloc[0]):
#                grid_square = grid_square.intersection(gdf.geometry.iloc[0])
#                grid_polygons.append(grid_square)
    
    # Create a GeoDataFrame from the grid polygons
    grid_gdf = gpd.GeoDataFrame(geometry=grid_polygons, crs=gdf.crs)
      
    # Step 9: Rotate back and reproject the grid with the original tilt and coordinate reference system
    rotated_geometries = [rotate(geometry, angle, origin=centroid) for geometry in grid_gdf['geometry']]
    grid_gdf['geometry'] = rotated_geometries

    # Step 8: Shift the grid polygons to the center of the original frame polygon
    grid_gdf_dissolve = grid_gdf.dissolve()
    grid_centroid = (grid_gdf_dissolve["geometry"].centroid.x, grid_gdf_dissolve["geometry"].centroid.y)
    centroid_x_offset = centroid[0] - grid_centroid[0]
    centroid_y_offset = centroid[1] - grid_centroid[1]
    grid_gdf = grid_gdf.translate(xoff=centroid_x_offset, yoff=centroid_y_offset)

    # Step 10: Export the grid to shapefile
    grid_gdf = grid_gdf.to_crs(orig_crs)
    grid_gdf.to_file(grid_output_shp)
