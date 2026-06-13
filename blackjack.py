import time
from configs.app_config import EARLY_EXIT_SLEEP
from configs.rules_config import MIN_BET, MAX_BET, MAX_TOTAL_VALUE
from configs.input_config import DEFAULT_PLAYER_NAME, CHIPS_DICT
from utils.swiss_knife import find_ordinal, find_placed_insurance, remind_betting_amount, find_total_bets
from widgets.layouts import set_cards_tabs
from widgets.interactions import get_chips, get_early_pay, get_insurance, get_move
from widgets.notifications import notify_inadequate_capital, update_cumulated_capital, notify_early_exit
from widgets.chips import return_chips
from machines.shuffle_machine import ShuffleMachine
from roles.dealer import Dealer
from roles.player import Player


class Blackjack:
    """
    A class to serve as Blackjack game.

    Attributes:
        machine (ShuffleMachine): shuffle machine.
        dealer (Dealer): dealer in Blackjack.
        player (Player): player in Blackjack.
        capital (int): player's current capital.
        player_name (str): name of player.
        chips_list (list): list of chips placed by player.
        insurance_hands_list (list): list of hands that player has placed insurance on.
        first_two_cards_list (list[list]): list to store list of first two cards and suits for each hand.
        non_early_bj_hands_list (list): list of hands that declined early pay.
        final_head_hands_list (list): list of final head hands.

    Methods:
        check_chips(chips: int): check if placed bets are valid.
        check_insurance(insurance_hands_list: list[str]): check if wanted insurance amount is valid.
        set_up(head_hands: int, capital: int, player_name: str = None): set up game.
        start(): start a new round of game.
    """

    def __init__(self):
        """Initialize Blackjack game by setting up required attributes."""
        self.machine = ShuffleMachine()
        self.dealer, self.player = Dealer(), Player()

        self.capital, self.player_name = 0, DEFAULT_PLAYER_NAME
        self.chips_list, self.insurance_hands_list = [], []

        self.first_two_cards_list = []
        self.non_early_bj_hands_list = []
        self.final_head_hands_list = []

    def check_chips(self, chips: int):
        """
        Check if placed bets are valid. Function is defined here to receive updating attributes.

        Args:
            chips (int): amount of chips placed.

        Returns:
            str: a message indicating if placed bets are valid.
        """
        if chips < MIN_BET:
            return f"Placed chips must >= minimum bet {str(MIN_BET)}."
        if chips > MAX_BET:
            return f"Placed chips must <= maximum bet {str(MAX_BET)}."
        if chips > self.capital:
            return f"Placed chips must <= remaining capital {str(self.capital)}."
        if chips % 100 != 0:
            return "Placed chips must be in units of 100."

    def check_insurance(self, insurance_hands_list: list[str]):
        """
        Check if insurance amount is valid. Function is defined here to receive updating attributes.

        Args:
            insurance_hands_list (list[str]): list of hands that player wants to place insurance on.

        Returns:
            str: a message indicating if wanted insurance amount is valid.
        """
        insurance = find_placed_insurance(
            find_ordinal(insurance_hands_list), self.player.hands_dict
        )
        if insurance > self.capital:
            return f"Your wanted insurance {insurance} > remaining capital {str(self.capital)}. Please reselect."

    def set_up(self, head_hands: int, capital: int, player_name: str = None):
        """
        Set up game.

        Args:
            head_hands (int): number of head hands.
            capital (int): player's capital.
            player_name (str, optional): name of player. Defaults to None.
        """
        self.capital = capital
        self.machine.load_and_shuffle()

        if player_name is not None:  # If player does enter name, make updates.
            self.player_name = player_name

        self.chips_list.clear()
        chips_dict = CHIPS_DICT.copy()  # Make a copy to prevent changing config.
        for i in range(1, head_hands + 1):
            if self.capital < MIN_BET:  # Remaining capital isn't enough for another head hand.
                notify_inadequate_capital(self.capital, no_more_hand=True)
                break

            chips_dict.update({"label": f"{CHIPS_DICT['label']} {i}:"})
            chips_dict.update(  # Update holder text w.r.t. to remaining capital as max feasible bet.
                {"holder": f"{CHIPS_DICT['holder']} {remind_betting_amount(self.capital)}"}
            )

            chips = get_chips(chips_dict, self.check_chips)
            self.capital -= chips  # Deduct chips amount from capital.
            self.chips_list.append(chips)
            update_cumulated_capital(self.player_name, self.capital)

        first_card, first_suit = self.machine.draw()
        self.dealer.prepare(first_card, first_suit)
        set_cards_tabs(len(self.chips_list))  # Open tabs for all existing head hands.

        self.first_two_cards_list.clear()
        for _ in range(len(self.chips_list)):  # Deal cards to these head hands.
            self.first_two_cards_list.append(list(self.machine.draw(True)))
        self.player.prepare(self.chips_list, self.first_two_cards_list)

    def start(self):
        """
        Start a new round.

        Returns:
            int: total bets placed by player.
        """
        self.non_early_bj_hands_list.clear()
        bj_hands_list = sorted(
            filter(
                lambda x: self.player.hands_dict[x].blackjack,
                self.player.hands_dict.keys(),
            ),
            reverse=True,
        )  # Sort by higher to lower ordinal.

        for bj_hand_ordinal in bj_hands_list:
            if self.dealer.early_pay:  # If dealer checks early pay.
                if get_early_pay(bj_hand_ordinal) == "take":  # Accepted early pay.
                    self.capital += return_chips(
                        bj_hand_ordinal,
                        player_bj=True,
                        early_pay=True,
                        chips=self.player.hands_dict[bj_hand_ordinal].initial_chips,
                    )
                    update_cumulated_capital(self.player_name, self.capital)
                    continue  # Go to next Blackjack head hand.

                self.non_early_bj_hands_list.append(bj_hand_ordinal)  # Declined early pay.
                continue  # Go to next Blackjack head hand.

            # If dealer has 0 Blackjack chance.
            self.capital += return_chips(
                bj_hand_ordinal,
                player_bj=True,
                chips=self.player.hands_dict[bj_hand_ordinal].initial_chips,
            )
            update_cumulated_capital(self.player_name, self.capital)

        self.insurance_hands_list.clear()
        non_bj_head_hands_list = sorted(
            filter(
                lambda x: self.player.hands_dict[x].blackjack is False,
                self.player.hands_dict.keys(),
            )
        )

        if len(non_bj_head_hands_list) > 0:  # Pass function to validate insurance.
            self.insurance_hands_list += find_ordinal(
                get_insurance(
                    self.dealer.cards_list[0],
                    non_bj_head_hands_list,
                    self.player.hands_dict,
                    self.check_insurance,
                )
            )
            self.player.update_insurance(self.insurance_hands_list)

            if len(self.insurance_hands_list) > 0:
                self.capital -= find_placed_insurance(
                    self.insurance_hands_list, self.player.hands_dict
                )  # Deduct insurance from capital.
                update_cumulated_capital(self.player_name, self.capital)

            head_ordinal = non_bj_head_hands_list[0]  # Start from the lowest ordinal.
            while True:  # Iterate through all head hands.
                if head_ordinal not in non_bj_head_hands_list:
                    break  # If all head hands are played, end head iteration.

                head_hand_object = self.player.hands_dict[head_ordinal]
                initial_chips = self.player.hands_dict[head_ordinal].initial_chips

                branches_list = list(head_hand_object.cards_dict.keys())  # Branches of iterated head hand.
                branch_ordinal = "1"  # Start from 1st branch.

                while True:  # Iterate through all branches.
                    if branch_ordinal not in branches_list:
                        break  # All branches are played: end branch iteration and go to next head.

                    move = get_move(
                        (head_ordinal, branch_ordinal),
                        head_hand_object.cards_dict[branch_ordinal],
                        self.dealer.cards_list[0],
                        head_hand_object.splits,
                        self.capital,
                        initial_chips,
                    )

                    if move == "surrender":
                        self.capital += return_chips(
                            head_ordinal, chips=initial_chips, surrender=True
                        )
                        update_cumulated_capital(self.player_name, self.capital)
                        head_hand_object.surrender()
                        break  # End branch iteration and go to next head.

                    if move in ["stand", "double_down"]:
                        if move == "stand":
                            head_hand_object.stand(branch_ordinal)

                        if move == "double_down":  # Deduct additional bet from capital.
                            self.capital -= initial_chips
                            update_cumulated_capital(self.player_name, self.capital)
                            drawn_card, drawn_suit = self.machine.draw()
                            head_hand_object.hit_or_double_down(
                                drawn_card, drawn_suit, branch_ordinal, True
                            )

                            if head_hand_object.bust_dict[branch_ordinal]:
                                return_chips(  # Display busted loss.
                                    head_ordinal,
                                    branch_ordinal=branch_ordinal,
                                    player_bust=True,
                                    chips=head_hand_object.chips_dict[branch_ordinal],
                                )

                        # For split branch, reload closest isolated branch and update list.
                        if head_hand_object.splits > 0:
                            drawn_card, drawn_suit = self.machine.draw()
                            head_hand_object.reload(drawn_card, drawn_suit, branch_ordinal)
                            branches_list = list(head_hand_object.cards_dict.keys())

                        if branch_ordinal == branches_list[-1]:
                            break  # Last branch: end branch iteration and go to next head.

                        # Otherwise, go to next branch.
                        branch_ordinal = branches_list[branches_list.index(branch_ordinal) + 1]

                    if move == "hit":  # If hit is chosen.
                        drawn_card, drawn_suit = self.machine.draw()
                        head_hand_object.hit_or_double_down(
                            drawn_card, drawn_suit, branch_ordinal
                        )
                        bust_mark = head_hand_object.bust_dict[branch_ordinal]

                        if bust_mark | (head_hand_object.value_dict[branch_ordinal] == MAX_TOTAL_VALUE):
                            if bust_mark:
                                return_chips(  # Display busted loss.
                                    head_ordinal,
                                    branch_ordinal=branch_ordinal,
                                    player_bust=True,
                                    chips=head_hand_object.chips_dict[branch_ordinal],
                                )

                            # For split branch, reload closest isolated branch and update list.
                            if head_hand_object.splits > 0:
                                drawn_card, drawn_suit = self.machine.draw()
                                head_hand_object.reload(drawn_card, drawn_suit, branch_ordinal)
                                branches_list = list(head_hand_object.cards_dict.keys())

                            if branch_ordinal == branches_list[-1]:
                                break  # For last branch, end branch iteration and go to next head.

                            # Otherwise, go to next branch.
                            branch_ordinal = branches_list[branches_list.index(branch_ordinal) + 1]

                    if move == "split":  # Deduct additional bet from capital.
                        self.capital -= initial_chips
                        update_cumulated_capital(self.player_name, self.capital)

                        drawn_card, drawn_suit = self.machine.draw()
                        head_hand_object.split(drawn_card, drawn_suit, branch_ordinal)
                        if head_hand_object.aces_pair:  # Aces pair is being split.
                            drawn_card, drawn_suit = self.machine.draw()
                            head_hand_object.reload(drawn_card, drawn_suit, branch_ordinal)
                            break  # Reload 2nd branch. Break branch iteration and go to next head.

                if head_ordinal == non_bj_head_hands_list[-1]:
                    break  # Last head hand: end head iteration.

                # Otherwise, go to next head hand.
                head_ordinal = non_bj_head_hands_list[non_bj_head_hands_list.index(head_ordinal) + 1]

        self.final_head_hands_list.clear()
        # Head hands with 1+ branch that isn't Blackjack, surrendered or busted.
        for head_ordinal in self.player.hands_dict.keys():
            if self.player.hands_dict[head_ordinal].blackjack is False:
                if self.player.hands_dict[head_ordinal].surrendered is False:
                    if not all(self.player.hands_dict[head_ordinal].bust_dict.values()):
                        self.final_head_hands_list.append(head_ordinal)

        check_blackjack_only = False
        if len(self.final_head_hands_list) == 0:  # Remaining hands only need to see if dealer has Blackjack.
            if len(self.non_early_bj_hands_list + self.insurance_hands_list) > 0:
                check_blackjack_only = True

        # Add non-early-paid Blackjack hands into final head hands list.
        self.final_head_hands_list += self.non_early_bj_hands_list

        # Add hands with insurance into final head hands list. Make sure items are distinct.
        for insurance_head_ordinal in self.insurance_hands_list:
            if insurance_head_ordinal not in self.final_head_hands_list:
                self.final_head_hands_list.append(insurance_head_ordinal)

        if len(self.final_head_hands_list) == 0:  # If no remaining hands to be judged.
            notify_early_exit()
            time.sleep(EARLY_EXIT_SLEEP)
            return find_total_bets(self.player.hands_dict, self.insurance_hands_list)

        self.dealer.add_to_17_plus(self.machine, check_blackjack_only)

        for head_ordinal in self.final_head_hands_list:
            head_hand_object = self.player.hands_dict[head_ordinal]  # Head hand object.
            branches_list = list(
                filter(
                    lambda x: head_hand_object.bust_dict[x] is False,
                    head_hand_object.cards_dict.keys(),
                )
            )  # List of branches that aren't busted.

            if len(branches_list) == 0:  # Empty: iterated head hand must be awaiting insurance result.
                branches_list.append("1")  # Add 1st ordinal into list.

            for branch_ordinal in branches_list:
                branch_insurance = 0  # Pay insurance to 1st branch if dealer's Ace becomes Blackjack.
                if (head_ordinal in self.insurance_hands_list) & (branch_ordinal == "1"):
                    branch_insurance = 1 if self.dealer.blackjack else -1

                branch_chips = head_hand_object.chips_dict[branch_ordinal]
                branch_bust = head_hand_object.bust_dict[branch_ordinal]
                branch_value = head_hand_object.value_dict[branch_ordinal]

                self.capital += return_chips(
                    head_ordinal,
                    branch_ordinal,
                    branch_chips,
                    False,
                    False,
                    branch_insurance,
                    head_hand_object.blackjack,
                    self.dealer.blackjack,
                    branch_bust,
                    branch_value,
                    self.dealer.value,
                )

        update_cumulated_capital(self.player_name, self.capital)
        return find_total_bets(self.player.hands_dict, self.insurance_hands_list)
