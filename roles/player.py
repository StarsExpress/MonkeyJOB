from machines.hand_processor import HandProcessor


class Player:
    """
    A class to serve as Blackjack player.

    Attributes:
        hands_dict: dictionary of each hand's cards.

    Methods:
        prepare(chips_list: list[int], cards_and_suits_list: list[list[str]]): load cards for new round.
    """

    def __init__(self) -> None:
        """Initialize a new instance of Player class."""
        self.hands_dict: dict[str, HandProcessor] = dict()

    def prepare(self, chips_list: list[int], cards_and_suits_list: list[list[str]]) -> None:
        """
        Prepare player's hands for a new round.

        Args:
            chips_list (list[int]): list of chips for each hand.
            cards_and_suits_list (list[list[str]]): list of cards and suits for each hand.
        """
        self.hands_dict.clear()  # Clear dictionaries before loading values.

        for idx, chips in enumerate(chips_list):
            self.hands_dict.update(
                {
                    str(idx + 1): HandProcessor(
                        str(idx + 1),
                        chips,
                        cards_and_suits_list[idx][:2],  # First 2 items are cards.
                        cards_and_suits_list[idx][-2:],  # Last 2 items are suits.
                    )
                }
            )
            self.hands_dict[str(idx + 1)].display_properties()
