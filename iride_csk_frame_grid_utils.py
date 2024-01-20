u"""
Written by Jonas Cinquini
January 2024

Set of Utilities to process a shapefile, create grids within polygons,
and save the result.

Python Dependencies
geopandas: Open source project to make working with geospatial data
    in python easier: https://geopandas.org
pyproj: Python interface to PROJ (cartographic projections and coordinate
    transformations library):
    https://pyproj4.github.io/pyproj/stable/index.html
shapely: Python package for manipulation and analysis of planar geometric
    objects: https://shapely.readthedocs.io/en/stable/
"""
import math
import geopandas as gpd
from pyproj import CRS, Transformer
from shapely.ops import transform
from shapely.geometry import Polygon
from shapely.affinity import rotate
from math import ceil


def add_frame_code_field(grid_gdf):
    """
    Add a new field "f_code" to the grid GeoDataFrame and populate
    each polygon with a code.

    Parameters:
        grid_gdf (GeoDataFrame): Input GeoDataFrame containing
            the grid polygons.

    Returns:
        GeoDataFrame: GeoDataFrame with the added "f_code" field.
    """
    # Sort the polygons based on their coordinates
    sorted_polygons = sorted(grid_gdf['geometry'],
                             key=lambda geom: (geom.bounds[1], geom.bounds[0]))

    # Add a new field "f_code" and populate with codes
    grid_gdf['f_code'] = range(1, len(grid_gdf) + 1)

    return grid_gdf


def reproject_geodataframe(gdf: gpd.GeoDataFrame, target_epsg: int) \
        -> gpd.GeoDataFrame:
    """
    Projects a Shapely polygon within a GeoDataFrame to a target EPSG code.

    Parameters:
    - gdf (geopandas.GeoDataFrame): Input GeoDataFrame containing the polygon.
    - target_epsg (int): Target EPSG code for the coordinate transformation.

    Returns:
    - geopandas.GeoDataFrame: Reprojected GeoDataFrame.
    """
    # Check if the geometry column exists and contains polygons
    if ('geometry' not in gdf.columns or
            gdf['geometry'].geom_type.any() == 'Polygon'):
        raise ValueError("Input GeoDataFrame must contain a "
                         "'geometry' column with Polygon geometries.")

    # Create a copy of the GeoDataFrame to avoid modifying the original
    gdf_copy = gdf.copy()

    # Set up coordinate reference systems
    source_crs = gdf.crs
    target_crs = CRS.from_epsg(target_epsg)

    # Create a transformer for the coordinate transformation
    transformer = Transformer.from_crs(source_crs, target_crs, always_xy=True)

    # Reproject each polygon in the 'geometry' column
    gdf_copy['geometry'] \
        = gdf_copy['geometry'].apply(lambda geom:
                                     transform(transformer.transform, geom))

    # Update the GeoDataFrame's coordinate reference system
    gdf_copy.crs = target_crs

    return gdf_copy


def get_fishnet_grid(xmin: float, ymin: float, xmax: float, ymax: float,
                     gridWidth: float, gridHeight: float) -> gpd.GeoDataFrame:
    """
    Generate a fishnet grid of polygons within the specified bounding box.

    Parameters:
        xmin (float): Minimum x-coordinate of the bounding box.
        ymin (float): Minimum y-coordinate of the bounding box.
        xmax (float): Maximum x-coordinate of the bounding box.
        ymax (float): Maximum y-coordinate of the bounding box.
        gridWidth (float): Width of each grid cell.
        gridHeight (float): Height of each grid cell.

    Returns:
        gdf (GeoDataFrame): GeoDataFrame containing the fishnet grid polygons.
    """
    # Get the number of rows and columns
    rows = ceil((ymax - ymin) / gridHeight)
    cols = ceil((xmax - xmin) / gridWidth)

    polygons = []

    # Generate polygons within the bounding box
    for i in range(cols):
        for j in range(rows):
            left = xmin + i * gridWidth
            right = left + gridWidth
            top = ymax - j * gridHeight
            bottom = top - gridHeight

            polygon = Polygon([(left, top), (right, top), (right, bottom),
                               (left, bottom), (left, top)])
            polygons.append(polygon)

    # Create a GeoDataFrame with the generated polygons
    gdf = gpd.GeoDataFrame(geometry=polygons, crs='EPSG:3857')
    return gdf


def rotate_polygon_to_north_up(geometry):
    """
    Rotate a polygon to align its orientation with the north.

    Parameters:
        geometry (Polygon): Input polygon.

    Returns:
        rotated_geometry (Polygon): Rotated polygon.
        angle (float): Angle of rotation.
    """
    exterior_coords_list = geometry.exterior.coords[:-1]
    p1 = min(exterior_coords_list, key=lambda t: t[0])
    ind_p1 = exterior_coords_list.index(p1)
    p2 = exterior_coords_list[ind_p1+1]

    angle = math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0]))
    centroid = (geometry.centroid.x, geometry.centroid.y)
    rotated_geometry = rotate(geometry, -angle, origin=centroid)

    return rotated_geometry, angle


def create_grid_within_polygon(geometry, x_frame_split, y_frame_split):
    """
    Create a grid of polygons within the rotated bounding box of a polygon.

    Parameters:
        geometry (Polygon): Input polygon.
        x_frame_split (int): Number of columns in the grid.
        y_frame_split (int): Number of rows in the grid.

    Returns:
        grid_gdf (GeoDataFrame): GeoDataFrame containing the grid polygons.
    """
    rotated_geometry, angle = rotate_polygon_to_north_up(geometry)
    min_x, min_y, max_x, max_y = rotated_geometry.bounds
    print(f"\n\nmin x: {min_x}\nmin y: {min_y}\nmax_x: "
          f"{max_x}\nmax_y: {max_y}")

    x_spacing = (max_x - min_x) / x_frame_split
    y_spacing = (max_y - min_y) / y_frame_split

    grid_gdf = get_fishnet_grid(min_x, min_y, max_x, max_y,
                                gridWidth=x_spacing, gridHeight=y_spacing)

    # Rotate each grid cell back to the original orientation
    rotated_geometries = [rotate(geometry, angle,
                                 origin=(rotated_geometry.centroid.x,
                                         rotated_geometry.centroid.y))
                          for geometry in grid_gdf['geometry']]

    grid_gdf['geometry'] = rotated_geometries
    return grid_gdf


def grid_gdf_shift(input_gdf: gpd.GeoDataFrame,
                   x_y_reference: tuple) -> gpd.GeoDataFrame:
        """
        Applies a shift on the dataframe based on centroid offset.
        The offset is calculated from a tuple reference coordinates
        and gdf centroid.
        """
        grid_gdf_dissolve = input_gdf.dissolve()
        grid_centroid = (grid_gdf_dissolve["geometry"].centroid.x,
                         grid_gdf_dissolve["geometry"].centroid.y)
        centroid_x_offset = x_y_reference[0] - grid_centroid[0]
        centroid_y_offset = x_y_reference[1] - grid_centroid[1]
        grid_gdf = input_gdf.translate(xoff=float(centroid_x_offset),
                                       yoff=float(centroid_y_offset))
        grid_gdf = gpd.GeoDataFrame(geometry=gpd.GeoSeries(grid_gdf))

        return grid_gdf
