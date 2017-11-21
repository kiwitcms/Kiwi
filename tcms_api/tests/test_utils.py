import unittest

import tcms_api


class TestIdify(unittest.TestCase):
    def test_idify_from_int_retruns_list(self):
        self.assertEqual([1, 2], tcms_api.base._idify(1000000002))

    def test_idify_from_list_retruns_int(self):
        self.assertEqual(1000000002, tcms_api.base._idify([1, 2]))
