import unittest
from collections import Counter
from configs.rules_config import CARDS_LIST, NUMBER_OF_DECKS, SUITS
from machines.shuffle_machine import ShuffleMachine


class TestShuffleMachine(unittest.TestCase):
    """Test methods of ShuffleMachine class."""
    def setUp(self) -> None:
        """Store shuffle machine in the test class."""
        self.machine = ShuffleMachine()

    def test_load_and_shuffle(self) -> None:
        """Test functionality of load_and_shuffle."""
        self.machine.load_and_shuffle()
        cards_dict = dict(Counter(self.machine.cards_list))
        self.assertEqual(cards_dict.keys(), set(CARDS_LIST))
        self.assertEqual(set(cards_dict.values()), {4 * NUMBER_OF_DECKS})

    def test_draw(self) -> None:
        """Test functionality of draw."""
        self.machine.load_and_shuffle()
        drawn_cards_suits: list[tuple] = [self.machine.draw()]

        drawn_card_1, drawn_card_2, drawn_suit_1, drawn_suit_2 = self.machine.draw(True)
        drawn_cards_suits.extend(
            [(drawn_card_1, drawn_suit_1), (drawn_card_2, drawn_suit_2)]
        )

        for drawn_card, drawn_suit in drawn_cards_suits:
            self.machine.cards_list.append(drawn_card)
            self.machine.suits_dict[drawn_card].append(drawn_suit)

        cards_dict = dict(Counter(self.machine.cards_list))
        self.assertEqual(cards_dict.keys(), set(CARDS_LIST))
        self.assertEqual(set(cards_dict.values()), {4 * NUMBER_OF_DECKS})
        for card in cards_dict.keys():
            suits_dict = dict(Counter(self.machine.suits_dict[card]))
            self.assertEqual(suits_dict.keys(), set(SUITS))
            self.assertEqual(set(suits_dict.values()), {NUMBER_OF_DECKS})


if __name__ == "__main__":
    unittest.main()
