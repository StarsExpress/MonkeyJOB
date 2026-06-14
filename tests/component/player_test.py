import unittest
from roles.player import Player


class TestPlayer(unittest.TestCase):
    """Test Player.prepare loads hands for a new round."""

    def setUp(self):
        self.player = Player()

    def test_single_hand_entry(self):
        self.player.prepare([500], [['A', 'K', 'S', 'H']])

        self.assertEqual(len(self.player.hands_dict), 1)
        self.assertIn('1', self.player.hands_dict)

    def test_multiple_hands_entries(self):
        self.player.prepare([500, 600], [['A', 'K', 'S', 'H'], ['7', '8', 'D', 'C']])

        self.assertEqual(len(self.player.hands_dict), 2)
        self.assertIn('1', self.player.hands_dict)
        self.assertIn('2', self.player.hands_dict)

    def test_clear_previous_hands(self):
        self.player.prepare([500], [['A', 'K', 'S', 'H']])
        self.player.prepare([600], [['7', '8', 'D', 'C']])

        self.assertEqual(len(self.player.hands_dict), 1)
        self.assertEqual(self.player.hands_dict['1'].cards_dict['1'], ['7', '8'])

    def test_chips_assignments(self):
        self.player.prepare([500], [['A', 'K', 'S', 'H']])
        self.assertEqual(self.player.hands_dict['1'].initial_chips, 500)

        self.player.prepare([300, 700], [["5", "6", "S", "H"], ["9", "9", "D", "C"]])
        self.assertEqual(self.player.hands_dict["1"].initial_chips, 300)
        self.assertEqual(self.player.hands_dict["2"].initial_chips, 700)

    def test_cards_assignments(self):
        self.player.prepare([500], [['7', '8', 'D', 'C']])
        self.assertEqual(self.player.hands_dict['1'].cards_dict['1'], ['7', '8'])

    def test_suits_assignments(self):
        self.player.prepare([500], [['7', '8', 'D', 'C']])
        self.assertEqual(self.player.hands_dict['1'].suits_dict['1'], ['D', 'C'])

    def test_blackjack_detection(self):
        self.player.prepare([500], [['A', 'K', 'S', 'H']])
        self.assertTrue(self.player.hands_dict['1'].blackjack)

        self.player.prepare([500], [['7', '8', 'D', 'C']])
        self.assertFalse(self.player.hands_dict['1'].blackjack)

    def test_1_indexed_hand_ordinals(self):
        self.player.prepare([500, 500, 500], [
            ['2', '3', 'S', 'H'],
            ['4', '5', 'D', 'C'],
            ['6', '7', 'S', 'D'],
        ])

        self.assertIn('1', self.player.hands_dict)
        self.assertIn('2', self.player.hands_dict)
        self.assertIn('3', self.player.hands_dict)


if __name__ == '__main__':
    unittest.main()
