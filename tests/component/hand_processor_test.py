import unittest
from machines.hand_processor import HandProcessor


class TestInitialization(unittest.TestCase):
    """Test HandProcessor.__init__ initializes state correctly."""

    def test_hand_states(self):
        hand_processor = HandProcessor('1', 500, ['7', '8'], ['S', 'H'])
        self.assertEqual(hand_processor.head_ordinal, '1')
        self.assertEqual(hand_processor.initial_chips, 500)
        self.assertEqual(hand_processor.splits, 0)
        self.assertEqual(hand_processor.insurance, 0)
        self.assertFalse(hand_processor.blackjack)
        self.assertFalse(hand_processor.surrendered)
        self.assertFalse(hand_processor.aces_pair)

    def test_hand_dicts(self):
        hand_processor = HandProcessor('1', 500, ['7', '8'], ['S', 'H'])
        self.assertEqual(hand_processor.chips_dict, {'1': 500})
        self.assertEqual(hand_processor.double_down_dict, {'1': False})
        self.assertEqual(hand_processor.cards_dict, {'1': ['7', '8']})
        self.assertEqual(hand_processor.suits_dict, {'1': ['S', 'H']})

    def test_hand_properties(self):
        hand_processor = HandProcessor('1', 500, ['7', '8'], ['S', 'H'])
        self.assertEqual(hand_processor.value_dict['1'], 15)
        self.assertFalse(hand_processor.soft_dict['1'])
        self.assertFalse(hand_processor.bust_dict['1'])

    def test_blackjack_detection(self):
        hand_processor = HandProcessor('1', 500, ['A', 'K'], ['S', 'H'])
        self.assertTrue(hand_processor.blackjack)
        self.assertFalse(hand_processor.aces_pair)

        hand_processor = HandProcessor('1', 500, ['10', 'A'], ['S', 'H'])
        self.assertTrue(hand_processor.blackjack)

        hand_processor = HandProcessor('1', 500, ['A', '9'], ['S', 'H'])
        self.assertFalse(hand_processor.blackjack)

    def test_aces_pair_detection(self):
        hand_processor = HandProcessor('1', 500, ['A', 'A'], ['S', 'H'])
        self.assertTrue(hand_processor.aces_pair)
        self.assertFalse(hand_processor.blackjack)

    def test_soft_hand_value(self):
        hand_processor = HandProcessor('1', 500, ['A', '7'], ['S', 'H'])
        self.assertEqual(hand_processor.value_dict['1'], 18)
        self.assertTrue(hand_processor.soft_dict['1'])
        self.assertFalse(hand_processor.bust_dict['1'])

    def test_second_hand_ordinal(self):
        hand_processor = HandProcessor('2', 1000, ['Q', '9'], ['D', 'C'])
        self.assertEqual(hand_processor.head_ordinal, '2')
        self.assertEqual(hand_processor.initial_chips, 1000)


class TestSurrender(unittest.TestCase):
    """Test HandProcessor.surrender sets correct operations."""

    def setUp(self):
        self.hand_processor = HandProcessor('1', 500, ['Q', '6'], ['S', 'H'])

    def test_surrender_flag(self):
        self.assertFalse(self.hand_processor.surrendered)
        self.hand_processor.surrender()
        self.assertTrue(self.hand_processor.surrendered)

    def test_chips_immutability(self):
        self.hand_processor.surrender()
        self.assertEqual(self.hand_processor.chips_dict['1'], 500)

    def test_cards_immutability(self):
        self.hand_processor.surrender()
        self.assertEqual(self.hand_processor.cards_dict['1'], ['Q', '6'])


class TestHitOrDoubleDown(unittest.TestCase):
    """Test HandProcessor.hit_or_double_down correctly updates cards and state."""

    def setUp(self):
        self.hand_processor = HandProcessor('1', 500, ['7', '5'], ['S', 'H'])

    def test_hit_appends_card_and_suit(self):
        self.hand_processor.hit_or_double_down('6', 'D')
        self.assertEqual(self.hand_processor.cards_dict['1'], ['7', '5', '6'])
        self.assertEqual(self.hand_processor.suits_dict['1'], ['S', 'H', 'D'])

    def test_hit_updates_value(self):
        self.hand_processor.hit_or_double_down('6', 'D')  # 7 + 5 + 6 = 18.
        self.assertEqual(self.hand_processor.value_dict['1'], 18)

    def test_hit_bust_flag(self):
        self.hand_processor.hit_or_double_down('K', 'D')  # 7 + 5 + K = busted 22.
        self.assertTrue(self.hand_processor.bust_dict['1'])

    def test_hit_no_bust_flag(self):
        self.hand_processor.hit_or_double_down('4', 'D')  # 7 + 5 + 4 = 16. Not busted.
        self.assertFalse(self.hand_processor.bust_dict['1'])

    def test_hit_chips_immutability(self):
        self.hand_processor.hit_or_double_down('6', 'D')
        self.assertEqual(self.hand_processor.chips_dict['1'], 500)
        self.assertFalse(self.hand_processor.double_down_dict['1'])

    def test_double_down_doubles_chips(self):
        self.hand_processor.hit_or_double_down('4', 'D', double_down=True)
        self.assertEqual(self.hand_processor.chips_dict['1'], 1000)
        self.assertTrue(self.hand_processor.double_down_dict['1'])

    def test_double_down_bust_shows_double_chips(self):
        # 7 + 5 + K = busted 22.
        self.hand_processor.hit_or_double_down('K', 'D', double_down=True)
        self.assertTrue(self.hand_processor.bust_dict['1'])
        self.assertEqual(self.hand_processor.chips_dict['1'], 1000)

    def test_hit_on_named_branch(self):
        self.hand_processor.cards_dict['2'] = ['8']
        self.hand_processor.suits_dict['2'] = ['C']
        self.hand_processor.chips_dict['2'] = 500

        self.hand_processor.double_down_dict['2'] = False
        self.hand_processor.hit_or_double_down('9', 'H', branch_ordinal='2')

        self.assertEqual(self.hand_processor.cards_dict['2'], ['8', '9'])
        self.assertEqual(self.hand_processor.value_dict['2'], 17)

    def test_hit_soft_hand_turns_hard(self):
        hand_processor = HandProcessor('1', 500, ['A', '5'], ['S', 'H'])
        hand_processor.hit_or_double_down('K', 'D')  # A + 5 + 10 = hard 16.
        self.assertFalse(hand_processor.soft_dict['1'])
        self.assertEqual(hand_processor.value_dict['1'], 16)


class TestSplit(unittest.TestCase):
    """Test HandProcessor.split correctly creates a new branch and rearranges cards."""

    def setUp(self):
        self.hand_processor = HandProcessor('1', 500, ['8', '8'], ['S', 'H'])

    def test_split_creates_second_branch(self):
        self.hand_processor.split('7', 'D')
        self.assertIn('2', self.hand_processor.cards_dict)

    def test_first_branch_after_split(self):
        self.hand_processor.split('9', 'C')
        self.assertEqual(self.hand_processor.cards_dict['1'], ['8', '9'])

    def test_split_second_branch_has_split_card(self):
        self.hand_processor.split('9', 'C')
        self.assertEqual(self.hand_processor.cards_dict['2'], ['8'])

    def test_splits_counter(self):
        self.hand_processor.split('7', 'D')
        self.assertEqual(self.hand_processor.splits, 1)

    def test_split_updates_branch_value(self):
        self.hand_processor.split('9', 'C')  # 8 + 9' = 17.
        self.assertEqual(self.hand_processor.value_dict['1'], 17)

    def test_split_moves_suit_to_second_branch(self):
        self.hand_processor.split('9', 'C')
        self.assertEqual(self.hand_processor.suits_dict['2'], ['H'])  # second suit moved

    def test_aces_pair_split_marks_aces_pair(self):
        hand_processor = HandProcessor('1', 500, ['A', 'A'], ['S', 'H'])
        hand_processor.split('K', 'C')

        self.assertTrue(hand_processor.aces_pair)
        self.assertEqual(hand_processor.splits, 1)


class TestReload(unittest.TestCase):
    """Test HandProcessor.reload fills the next split branch with a second card."""

    def setUp(self):
        self.hand_processor = HandProcessor('1', 500, ['8', '8'], ['S', 'H'])
        self.hand_processor.split('J', 'C')  # Branch 1 = ['8', 'J']. Branch 2 = ['8'].

    def test_reload_appends_card_to_second_branch(self):
        self.hand_processor.reload('5', 'D', '1')  # next branch = '2'
        self.assertEqual(self.hand_processor.cards_dict['2'], ['8', '5'])

    def test_reload_appends_suit_to_second_branch(self):
        self.hand_processor.reload('5', 'D', '1')
        self.assertEqual(self.hand_processor.suits_dict['2'], ['H', 'D'])

    def test_reload_sets_branch_chips_as_initial(self):
        self.hand_processor.reload('5', 'D', '1')
        self.assertEqual(self.hand_processor.chips_dict['2'], 500)

    def test_reload_resets_double_down_flag(self):
        self.hand_processor.reload('5', 'D', '1')
        self.assertFalse(self.hand_processor.double_down_dict['2'])

    def test_reload_updates_branch_value(self):
        self.hand_processor.reload('5', 'D', '1')  # 8 + 5 = 13.
        self.assertEqual(self.hand_processor.value_dict['2'], 13)

    def test_reload_nonexistent_branch(self):
        self.hand_processor.reload('5', 'D', '2')  # next branch '3' doesn't exist

    def test_reload_branch_one_immutability(self):
        cards_before = list(self.hand_processor.cards_dict['1'])
        self.hand_processor.reload('5', 'D', '1')
        self.assertEqual(self.hand_processor.cards_dict['1'], cards_before)


if __name__ == '__main__':
    unittest.main()
