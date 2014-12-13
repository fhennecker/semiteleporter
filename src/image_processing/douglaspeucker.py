import numpy as np

def distance(d1, d2, p):
    """
    Return the distance between a line determined by points d1 and d2, and 
    a point p
    """
    u = d2-d1
    v = p-d1
    return np.linalg.norm(np.cross(u, v))/np.linalg.norm(u)

def douglas_peucker(points, thres, min=0, max=-1):
    """
    Apply douglas peucker algorithm in place, removing points from list by
    setting them to None.
    The Douglas-Peucker algorithm removes points from a polyline that are not
    significant (that is, if their distance from the main line is more than
    a given threshold).
    
    https://en.wikipedia.org/wiki/Ramer%E2%80%93Douglas%E2%80%93Peucker_algorithm
    """
    # Allows for negative indexing at first call
    if max < 0:
        max += len(points)

    # No points between min and max: finished
    if max-min <= 1:
        return

    # Otherwise, we find the most extreme point
    first, last = points[min], points[max]
    dmax, imax = 0, min
    for i in range(min+1, max):
        d = distance(first, last, points[i])
        if d > dmax:
            dmax, imax = d, i

    if dmax <= thres:
        # Most extreme point is below thresehold: remove all points
        for i in range(min+1, max):
            points[i] = None
    else:
        # Apply alogrithm on sublines
        douglas_peucker(points, thres, min, imax)
        douglas_peucker(points, thres, imax, max)

def reduce_pointset(points, thres=1):
    """
    Apply Douglas-Peucker algorithm on a laser point set to 
    reduce the number of points
    """
    if len(points) <= 2:
        return points
    # On ordonne les points verticalement
    points.sort(key=lambda x: x[2])
    douglas_peucker(points, thres)
    return filter(lambda x: x is not None, points)

### Tests (to be moved elsewhere) ###
def test_distance_point_to_line():
    D1, D2 = np.array([-1, 3, 4]), np.array([1, 3, 4])
    P = np.array([0, 0, 0])
    assert distance(D1, D2, P) == 5

def test_distance_point_to_line_aligned():
    D1, D2 = np.array([-1, 0, 0]), np.array([1, 0, 0])
    P = np.array([0, 0, 0])
    assert distance(D1, D2, P) == 0

def array_equal(A, B):
    """Helper function to compare 2 numpy arrays"""
    return not (A - B).any()

def test_reduce_pointset_3points():
    A, B, C = np.array([0, 0, 0]), np.array([2.5, 1, 6]), np.array([5, 0, 10])
    res = reduce_pointset([A, B, C], 2)
    assert len(res) == 2
    assert array_equal(A, res[0])
    assert array_equal(C, res[1])

def test_reduce_pointset_3points_keep():
    A, B, C = np.array([0, 0, 0]), np.array([2.5, 1, 1]), np.array([5, 0, 2])
    res = reduce_pointset([A, B, C], 0.5)
    assert len(res) == 3

def test_reduce_pointset_16points():
    points = map(np.array, zip(*[range(16) for i in range(3)]))
    points[8][0] = 42
    res = reduce_pointset(points)
    assert len(res) == 5

if __name__ == "__main__":
    # Collect tests if not using py.test
    _ = locals()
    is_a_test = lambda x: x.startswith('test_') and '__call__' in dir(_[x])
    for test_name in filter(is_a_test, _.keys()):
        _[test_name]()

