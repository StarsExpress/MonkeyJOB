import time
from configs.rules_config import MIN_DEALER_VALUE
from configs.app_config import DEALER_SLEEP
from utils.judges import judge_blackjack
from utils.trackers import update_properties
from widgets.cards import show_dealer_value
from machines.shuffle_machine import ShuffleMachine


class Dealer:
    """
    A class to serve as Blackjack dealer.

    Attributes:
        cards_list (list): list of cards in dealer's hand.
        suits_list (list): list of suits corresponding to cards.
        value (int): total value of dealer's hand.
        early_pay (bool): if dealer should offer early pay option to player.
        blackjack (bool): if dealer has Blackjack.
        soft (bool): if dealer has a soft hand.
        bust (bool): if dealer's hand is busted.

    Methods:
        prepare(first_card: str, first_suit: str): prepare dealer's hand for a new round.

        add_to_17_plus(shuffle_machine: ShuffleMachine, check_blackjack_only: bool = False):
        add cards to dealer's hand until total value is 17 or more (dealer needs 17+ except special cases).
    """

    def __init__(self):
        """Initialize a new instance of Dealer class. All booleans defaults to False."""
        self.cards_list, self.suits_list, self.value = [], [], 0  # Hand value starts from 0.
        self.early_pay, self.blackjack, self.soft, self.bust = False, False, False, False

    def prepare(self, first_card: str, first_suit: str):
        """
        Prepare dealer's hand for a new round.

        Args:
            first_card (str): first card of dealer's hand.
            first_suit (str): suit of first card.
        """
        self.cards_list.clear()  # Clear list before loading first card.
        self.cards_list.append(first_card)
        self.suits_list.clear()
        self.suits_list.append(first_suit)

        # If dealer may have Blackjack, early pay mode is on.
        self.early_pay = True if first_card in ["A", "K", "Q", "J", "10"] else False
        self.blackjack = False  # Reset Blackjack mark back to False.
        self.value, self.soft, self.bust = update_properties(self.cards_list)

        show_dealer_value(first_card, first_suit, value=self.value, soft=self.soft, first=True)

    def add_to_17_plus(self, shuffle_machine: ShuffleMachine, check_blackjack_only: bool = False):
        """
        Add cards to dealer's hand until total value is 17 or more except in special cases.

        Args:
            shuffle_machine (ShuffleMachine): shuffle machine to draw cards from.
            check_blackjack_only (bool, optional): if True, only check if dealer has a blackjack. Defaults to False.
        """
        while self.value < MIN_DEALER_VALUE:
            time.sleep(DEALER_SLEEP)  # Pause before drawing a new card.
            drawn_card, drawn_suit = shuffle_machine.draw()
            self.cards_list.append(drawn_card)
            self.suits_list.append(drawn_suit)

            if judge_blackjack(self.cards_list):  # Dealer has Blackjack.
                self.blackjack = True
                show_dealer_value(drawn_card, drawn_suit, blackjack=self.blackjack)
                return

            # If dealer has no Blackjack, stop drawing in either of two cases.
            # 1. Player's hands are all Blackjack. 2. Player's hands are all busted but have insurance.
            if check_blackjack_only:
                show_dealer_value(drawn_card, drawn_suit, check_bj_only=check_blackjack_only)
                return

            self.value, self.soft, self.bust = update_properties(self.cards_list)
            if self.bust:  # If dealer is busted, set value as 0 for chips calculation convenience.
                self.value = 0
                show_dealer_value(drawn_card, drawn_suit, bust=self.bust)
                return

            show_dealer_value(drawn_card, drawn_suit, value=self.value, soft=self.soft)
