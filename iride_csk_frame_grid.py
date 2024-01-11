import geopandas as gpd
from shapely.geometry import Polygon
from pyproj import Proj, transform
import math
from shapely.geometry import MultiPolygon
from shapely.affinity import rotate
from shapely.ops import unary_union

def get_frame_grid(input_frame_shp, grid_output_shp, buffer_dist=2000, x_spacing=25000, y_spacing=10000):
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
