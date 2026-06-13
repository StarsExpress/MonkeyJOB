from configs.rules_config import MAX_SPLITS
from utils.judges import judge_blackjack
from utils.trackers import update_properties
from widgets.cards import show_player_value
from widgets.notifications import remind_splits_rules


class HandProcessor:
    """
    A class to store card values and process surrender, stand, hit, double down and split for a given hand.

    Attributes:
        head_ordinal (str): ordinal of hand.
        initial_chips (int): amount of chips placed at start.
        insurance (int): amount of insurance.
        splits (int): number of splits.
        blackjack (bool): if hand is Blackjack.
        surrendered (bool): if hand is surrendered.
        aces_pair (bool): if hand is an Aces pair.
        chips_dict (dict): dictionary of chips for each branch.
        double_down_dict (dict): dictionary of double down status for each branch.
        cards_dict (dict): dictionary of cards for each branch.
        suits_dict (dict): dictionary of suits for each branch.
        value_dict (dict): dictionary of values for each branch.
        soft_dict (dict): dictionary of soft status for each branch.
        bust_dict (dict): dictionary of bust status for each branch.

    Methods:
        display_properties(branch_ordinal: str = '1'): display properties of a branch.
        surrender(): mark hand as surrendered.
        set_insurance_value(branch_ordinal: str = '1'): set insurance value for a branch.
        stand(branch_ordinal: str = '1'): mark a branch as committed stand.
        hit_or_double_down(card: str, suit: str, branch_ordinal: str = '1', double_down: bool = False):
        hit or double down a branch.
        split(card: str, suit: str, branch_ordinal: str = '1'): split a branch.
        reload(card: str, suit: str, branch_ordinal: str = '1'): reload a branch.
    """

    def __init__(self, head_ordinal: str, chips: int, cards_list: list[str], suits_list: list[str]):
        """
        Initialize HandProcessor with given parameters.

        Args:
            head_ordinal (str): ordinal of hand.
            chips (int): amount of chips placed at start. It helps track chips of "split" branches.
            cards_list (list[str]): list of cards of hand.
            suits_list (list[str]): list of suits corresponding to cards.
        """
        self.head_ordinal, self.initial_chips, self.insurance, self.splits = head_ordinal, chips, 0, 0

        self.blackjack, self.surrendered = judge_blackjack(cards_list), False
        self.aces_pair = True if cards_list == ['A', 'A'] else False  # Aces pair mark.

        self.chips_dict, self.double_down_dict = {'1': chips}, {'1': False}
        self.cards_dict, self.suits_dict = {'1': cards_list}, {'1': suits_list}

        value, soft, bust = update_properties(cards_list)
        self.value_dict, self.soft_dict, self.bust_dict = {'1': value}, {'1': soft}, {'1': bust}

    def display_properties(self, branch_ordinal: str = '1'):
        """
        Display properties of a branch.

        Args:
            branch_ordinal (str, optional): ordinal of branch. Defaults to '1'.
        """
        show_player_value(
            self.head_ordinal,
            branch_ordinal,
            cards_list=self.cards_dict[branch_ordinal],
            suits_list=self.suits_dict[branch_ordinal],
            value=self.value_dict[branch_ordinal],
            chips=self.chips_dict[branch_ordinal],
            insurance=self.insurance,
            blackjack=self.blackjack,
            soft=self.soft_dict[branch_ordinal],
            new_branch=True,
        )

    def surrender(self):
        """Mark the hand as surrendered."""
        self.surrendered = True

    def set_insurance_value(self, branch_ordinal: str = '1'):
        """
        Set insurance value for a branch. Insurance amount is 50% of initially placed bet.

        Args:
            branch_ordinal (str, optional): ordinal of branch. Defaults to '1'.
        """
        self.insurance = self.chips_dict['1'] // 2
        show_player_value(
            self.head_ordinal,
            branch_ordinal,
            chips=self.chips_dict['1'],
            insurance=self.insurance,
            update_chips=True,
            insurance_only=True,
        )

    def stand(self, branch_ordinal: str = '1'):
        """
        Mark a branch as committed stand. If the stood hand is soft, finalize its display value.

        Args:
            branch_ordinal (str, optional): ordinal of branch. Defaults to '1'.
        """
        if self.soft_dict[branch_ordinal]:
            show_player_value(
                self.head_ordinal,
                branch_ordinal,
                cards_list=self.cards_dict[branch_ordinal],
                value=self.value_dict[branch_ordinal],
                value_only=True,
                stand=True,
                soft=self.soft_dict[branch_ordinal],
            )

    def hit_or_double_down(self, card: str, suit: str, branch_ordinal: str = '1', double_down: bool = False):
        """
        Hit or double down a branch.

        Args:
            card (str): card to add.
            suit (str): suit of card.
            branch_ordinal (str, optional): ordinal of branch. Defaults to '1'.
            double_down (bool, optional): if double down is selected. Defaults to False.
        """
        self.cards_dict[branch_ordinal].append(card)  # Append a new card into the hand's list.
        self.suits_dict[branch_ordinal].append(suit)

        value, soft, bust = update_properties(self.cards_dict[branch_ordinal])
        self.value_dict[branch_ordinal] = value
        self.soft_dict[branch_ordinal], self.bust_dict[branch_ordinal] = soft, bust

        if double_down:
            self.chips_dict[branch_ordinal] *= 2
            self.double_down_dict[branch_ordinal] = True  # Switch double down mark to True.

        show_player_value(
            self.head_ordinal, branch_ordinal,
            cards_list=self.cards_dict[branch_ordinal],
            suits_list=self.suits_dict[branch_ordinal],
            value=value,
            insurance=self.insurance,
            stand=self.double_down_dict[branch_ordinal],
            soft=soft,
            bust=bust,
            chips=self.chips_dict[branch_ordinal],
            update_chips=self.double_down_dict[branch_ordinal],
        )

    def split(self, card: str, suit: str, branch_ordinal: str = '1'):
        """
        Split a branch. If Aces pair is split, stand right after split.

        Args:
            card (str): card to add.
            suit (str): suit of card.
            branch_ordinal (str, optional): ordinal of branch. Defaults to '1'.
        """
        stand = True if self.aces_pair else False
        self.cards_dict[str(self.splits + 2)] = [self.cards_dict[branch_ordinal][-1]]  # Move split card to new branch.
        self.cards_dict[branch_ordinal] = [self.cards_dict[branch_ordinal][0], card]

        self.suits_dict[str(self.splits + 2)] = [self.suits_dict[branch_ordinal][-1]]
        self.suits_dict[branch_ordinal] = [self.suits_dict[branch_ordinal][0], suit]

        value, soft, bust = update_properties(self.cards_dict[branch_ordinal])
        self.value_dict[branch_ordinal] = value
        self.soft_dict[branch_ordinal], self.bust_dict[branch_ordinal] = soft, bust

        show_player_value(
            self.head_ordinal,
            branch_ordinal,
            cards_list=self.cards_dict[branch_ordinal],
            suits_list=self.suits_dict[branch_ordinal],
            value=value,
            stand=stand,
            soft=soft,
            first_split=True,
        )

        self.splits += 1  # Add 1 to number of splits.
        if self.splits == MAX_SPLITS:
            remind_splits_rules(self.head_ordinal)

    def reload(self, card: str, suit: str, branch_ordinal: str = '1'):
        """
        Reload a new branch when split happens.

        Args:
            card (str): card to add.
            suit (str): suit of card.
            branch_ordinal (str, optional): ordinal of last complete (a.k.a. with 2+ cards) branch. Defaults to '1'.
        """
        branch_ordinal = str(int(branch_ordinal) + 1)  # The new branch to be reloaded.
        if branch_ordinal not in self.cards_dict.keys():
            return

        self.chips_dict[branch_ordinal], self.double_down_dict[branch_ordinal] = self.initial_chips, False
        self.cards_dict[branch_ordinal].append(card)
        self.suits_dict[branch_ordinal].append(suit)

        value, soft, bust = update_properties(self.cards_dict[branch_ordinal])
        self.value_dict[branch_ordinal] = value
        self.soft_dict[branch_ordinal], self.bust_dict[branch_ordinal] = soft, bust

        stand = True if self.aces_pair else False  # If the hand is Aces pair, stand right after reloading.
        show_player_value(
            self.head_ordinal, branch_ordinal,
            cards_list=self.cards_dict[branch_ordinal],
            suits_list=self.suits_dict[branch_ordinal],
            value=value,
            chips=self.chips_dict[branch_ordinal],
            stand=stand,
            soft=soft,
            new_branch=True,
        )
