import numpy as np
import pytest

from chalkline.calibration import Calibration


def test_rectifies_selected_board():
    image = np.zeros((100, 200, 3), dtype=np.uint8)
    image[20:80, 20:180] = 255
    cal = Calibration.create("test", 200, 100, 160, [[20, 20], [179, 20], [179, 79], [20, 79]])
    output = cal.rectify(image)
    assert output.shape[1] == 160
    assert output.mean() > 245


def test_rejects_crossed_points():
    with pytest.raises(ValueError):
        Calibration.create("test", 200, 100, 160, [[0, 0], [199, 99], [199, 0], [0, 99]])
