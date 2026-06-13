from pywebio.input import input_group, input, TEXT, NUMBER, slider, actions, checkbox
from configs.input_config import NAME_DICT, CAPITAL_DICT, HANDS_DICT, EARLY_PAY_DICT
from configs.input_config import INSURANCE_DICT, MOVES_DICT, CHOICES_DICT
from utils.input_validity import check_name, check_capital
from utils.judges import judge_surrender, judge_split
from utils.swiss_knife import assist_insurance_checkbox, find_ordinal_text


def get_info():
    """
    Get player's info: name and initial capital.

    Returns:
        dict: dict of player's name and initial capital.
    """
    return input_group(
        inputs=[
            input(
                label=NAME_DICT["label"],
                name=NAME_DICT["name"],
                type=TEXT,
                validate=check_name,
                placeholder=NAME_DICT["holder"],
            ),
            input(  # Initial capital is a required input.
                label=CAPITAL_DICT["label"],
                name=CAPITAL_DICT["name"],
                type=NUMBER,
                required=True,
                validate=check_capital,
                placeholder=CAPITAL_DICT["holder"],
            ),
        ]
    )


def get_hands():
    """
    Get number of hands to bet before each round.

    Returns:
        int: number of hands to bet.
    """
    return slider(
        label=HANDS_DICT["label"],
        min_value=HANDS_DICT["min"],
        max_value=HANDS_DICT["max"],
    )


def get_chips(chips_dict: dict[str, str], validate_function: callable):
    """
    Get chips placed by player for each hand.

    Args:
        chips_dict (dict[str, str]): contains label and placeholder for input.
        validate_function (callable): a function to validate input.

    Returns:
        int: number of chips placed by player.
    """
    return input(
        label=chips_dict["label"],
        type=NUMBER,
        required=True,
        validate=validate_function,
        placeholder=chips_dict["holder"],
    )


def get_early_pay(head_ordinal: str):
    """
    Get Blackjack early pay option.

    Args:
        head_ordinal (str): ordinal of head.

    Returns:
        str: chosen early pay option.
    """
    return actions(
        f"Hand {head_ordinal}: {EARLY_PAY_DICT['label']}",
        buttons=EARLY_PAY_DICT["options"],
    )


def get_insurance(
    dealer_first_card: str,
    non_bj_hands_list: list[str],
    hands_dict: dict[str],
    validate_function: callable,
):
    """
    Get insurance option.

    Args:
        dealer_first_card (str): first card of dealer.
        non_bj_hands_list (list[str]): list of non-Blackjack hands.
        hands_dict (dict[str]): dictionary of hands.
        validate_function (callable): function to validate input.

    Returns:
        list: list of selected insurance options.
    """
    if dealer_first_card != "A":  # No insurance needs to be asked.
        return []

    options_list = assist_insurance_checkbox(non_bj_hands_list, hands_dict)
    return checkbox(
        label=INSURANCE_DICT["label"],
        options=options_list,
        inline=True,
        value=non_bj_hands_list,
        validate=validate_function,
    )


def get_move(
    ordinals_tuple: tuple,
    cards_list: list[str],
    dealer_card: str,
    splits: int,
    remaining_capital: int,
    initial_bet: int,
):
    """
    Get player's move.

    Args:
        ordinals_tuple (tuple): contains hand ordinals with format: (head ordinal, branch ordinal).
        cards_list (list[str]): list of cards.
        dealer_card (str): dealer's card.
        splits (int): number of splits commited.
        remaining_capital (int): remaining capital.
        initial_bet (int): initial bet.

    Returns:
        str: selected move.
    """
    moves = []
    if judge_surrender(cards_list, dealer_card, splits):  # First check surrender availability.
        moves += [MOVES_DICT["surrender"]]

    moves += [MOVES_DICT["stand"], MOVES_DICT["hit"]]

    if remaining_capital >= initial_bet:  # Check double down and split availability.
        if len(cards_list) == 2:
            moves += [MOVES_DICT["double_down"]]
        if judge_split(cards_list, splits):
            moves += [MOVES_DICT["split"]]

    label = f"Hand {ordinals_tuple[0]}'s {find_ordinal_text(ordinals_tuple[-1])} "
    label += f"Branch: {MOVES_DICT['label']}"
    return actions(label, buttons=moves)


def get_choice():
    """
    Get choice of continue to play or start over.

    Returns:
        str: selected choice.
    """
    return actions(CHOICES_DICT["label"], buttons=CHOICES_DICT["choices"])
