from shapely.geometry import Polygon
from mita_csk_frame_grid_utils import rotate_polygon_to_north_up


def test_rotate_polygon_to_north_up():
    """
    Test the rotate_polygon_to_north_up function.
    """
    # Create a sample GeoDataFrame for testing
    polygon = Polygon([(12, 36), (11.5, 38), (14, 38.5),
                       (14, 36.5), (12, 36)])

    # Ensure the function runs without errors
    rotated_polygon, angle = rotate_polygon_to_north_up(polygon)

    # Perform assertions based on your expectations for the result
    assert isinstance(rotated_polygon, Polygon)
    assert isinstance(angle, float)
