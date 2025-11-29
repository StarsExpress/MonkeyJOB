from copy import deepcopy
import random
from random import shuffle
from configs.rules_config import NUMBER_OF_DECKS, CARDS_LIST, SUITS_DICT


class ShuffleMachine:
    """
    A class to shuffle and draw cards.

    Attributes:
        cards_list: list of cards in shuffle machine.
        suits_dict: dictionary of suits for each card type.

    Methods:
        load_and_shuffle(): refill cards and shuffle them.
        draw(two_cards: bool = False): draw 1 or 2 cards from deck's front.
        show_cards_count(): print each card's count if cards list isn't empty.
    """

    def __init__(self) -> None:
        """Initialize ShuffleMachine with empty list of cards and empty dictionary of suits."""
        self.cards_list = []
        self.suits_dict = {}

    def load_and_shuffle(self) -> None:
        """Refill cards list and shuffle them. Refill suits dictionary."""
        self.cards_list.clear()
        self.cards_list.extend(CARDS_LIST * NUMBER_OF_DECKS)
        shuffle(self.cards_list)
        self.suits_dict = deepcopy(SUITS_DICT)

    def draw(self, two_cards: bool = False) -> tuple:
        """
        Draw 1 or 2 cards from front of deck. Randomly select and remove a suit for each drawn card.

        Args:
            two_cards (bool, optional): if two cards are needed. Defaults to False.

        Returns:
            tuple: tuple of drawn card(s) and suit(s).
        """
        if two_cards:
            card_1 = self.cards_list.pop(0)
            card_2 = self.cards_list.pop(0)
            suit_1 = self.suits_dict[card_1].pop(random.randrange(len(self.suits_dict[card_1])))
            suit_2 = self.suits_dict[card_2].pop(random.randrange(len(self.suits_dict[card_2])))
            return card_1, card_2, suit_1, suit_2

        card = self.cards_list.pop(0)
        suit = self.suits_dict[card].pop(random.randrange(len(self.suits_dict[card])))
        return card, suit
