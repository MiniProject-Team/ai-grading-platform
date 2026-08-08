import unittest

import numpy as np

from smarthtr.core.entities import BoundingBox, Line
from smarthtr.reconstruction.reading_order import ReadingOrderReconstructor


class ReadingOrderTests(unittest.TestCase):
    def test_orders_top_to_bottom_then_left_to_right(self):
        image = np.zeros((2, 2, 3), dtype=np.uint8)
        lines = [Line(1, 1, BoundingBox(.8, .2, .9, .3), image), Line(2, 1, BoundingBox(.1, .1, .2, .2), image), Line(3, 1, BoundingBox(.1, .2, .2, .3), image)]
        self.assertEqual([line.id for line in ReadingOrderReconstructor().order(lines)], [2, 3, 1])
