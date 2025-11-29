import unittest
from parameterized import parameterized
from configs.rules_config import MAX_SPLITS
from utils.judges import judge_blackjack, judge_surrender, judge_split


class TestJudges(unittest.TestCase):
    """Test functionality of functions in judges.py."""
    @parameterized.expand([
        (["10", "A"], False, True),
        (["10", "A"], True, False),
        (["7", "7", "7"], True, False),
        (["7", "7", "7"], False, False)
    ])
    def test_blackjack_judge(self, cards, split, expected) -> None:
        """Test functionality of judge_blackjack."""
        self.assertEqual(judge_blackjack(cards, split), expected)

    @parameterized.expand([
        (["Q", "6"], "J", 0, True),
        (["Q", "6"], "J", 1, False),
        (["2", "6", "8"], "J", 0, False),
        (["2", "6", "8"], "J", 1, False),
        (["9", "9"], "A", 0, False),
        (["9", "9"], "A", 1, False)
    ])
    def test_surrender_judge(self, cards, dealer_card, splits, expected) -> None:
        """Test functionality of judge_surrender."""
        self.assertEqual(judge_surrender(cards, dealer_card, splits), expected)

    @parameterized.expand([
        (cards, splits, cards[0] == cards[1] and splits < MAX_SPLITS)
        for cards in [["8", "5"], ["8", "8"]]
        for splits in range(MAX_SPLITS + 1)
    ])
    def test_split_judge(self, cards, splits, expected) -> None:
        """Test functionality of judge_split."""
        self.assertEqual(judge_split(cards, splits), expected)


if __name__ == "__main__":
    unittest.main()
