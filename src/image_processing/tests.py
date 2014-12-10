import numpy as np
from filter import substract

def test_substract():
    imgA = np.array([[(23, 42, 246)]])
    imgB = np.array([[(23, 42, 22)]])
    delta = substract(imgA, imgB)
    assert delta.shape == (1, 1, 3)
    assert tuple(delta[0][0]) == (0, 0, 224)

def test_substract_img_changed():
    imgA = np.array([[(23, 42, 246)]])
    imgB = np.array([[(100, 123, 22)]])
    delta = substract(imgA, imgB)
    assert tuple(delta[0][0]) == (0, 0, 224)

if __name__ == "__main__":
    # Collect tests if not using py.test
    _ = locals()
    is_a_test = lambda x: x.startswith('test_') and '__call__' in dir(_[x])
    for test_name in filter(is_a_test, _.keys()):
        _[test_name]()
