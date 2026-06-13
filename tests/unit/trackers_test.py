import unittest
from utils.trackers import update_properties, track_display_value


class TestShuffleMachine(unittest.TestCase):
    """Test functionality of functions in trackers.py."""
    def test_update_properties(self):
        """Test functionality of update_properties."""
        self.assertEqual(update_properties(['A'] * 11), (21, True, False))
        self.assertEqual(update_properties(['A'] * 12), (12, False, False))

    def test_track_display_value(self):
        self.assertEqual(track_display_value(18, soft=True, stand=True), "18")
        self.assertEqual(track_display_value(18, soft=True, stand=False), "18/8")


if __name__ == "__main__":
    unittest.main()
