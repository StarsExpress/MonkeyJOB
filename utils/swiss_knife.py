from configs.rules_config import MAX_BET
from configs.output_config import VALUES_COLORS, DANGER_ZONE
from utils.trackers import track_display_value


def remind_betting_amount(remaining_capital: int):
    """
    Remind player of max feasible amount to bet for iterated hand.

    Args:
        remaining_capital (int): remaining capital of player.

    Returns:
        str: a string reminding player of max feasible bet.
    """
    return f"{str(min(remaining_capital, MAX_BET))}. Only accept 100's multiples."


def find_ordinal_text(ordinal: str):
    """
    Find corresponding text of an ordinal.

    Args:
        ordinal (str): ordinal to be converted to text.

    Returns:
        str: text representation of ordinal.
    """
    if ordinal == '1':
        return '1st'
    if ordinal == '2':
        return '2nd'
    if ordinal == '3':
        return '3rd'
    return '4th'  # Possible maximum branch is 4.


def assist_insurance_checkbox(non_bj_hands_list: list[str], hands_dict: dict):
    """
    Assist in creating options for insurance checkbox.

    Parameters:
        non_bj_hands_list (list[str]): list of non-Blackjack hands.
        hands_dict (dict): dictionary of hands.

    Returns:
        list: list of options for insurance checkbox.
    """
    options = []
    for head_ordinal in non_bj_hands_list:  # For each non-Blackjack hand, provide ordinal and displayed value.
        displayed_value = track_display_value(
            hands_dict[head_ordinal].value_dict['1'],
            soft=hands_dict[head_ordinal].soft_dict['1']
        )
        options.append(f"Hand {head_ordinal}: {displayed_value}")
    return options


def find_ordinal(insurance_hands_list: list[str]):
    """
    Get ordinal from checkbox option of this format: "Hand head_ordinal: displayed_value".

    Parameters:
        insurance_hands_list (list[str]): list of hands that have insurance.

    Returns:
        list: list of ordinals.
    """
    # [1] gets 1st item right next to 1st space. [:-1] excludes colon.
    return [head_ordinal.split(' ')[1][:-1] for head_ordinal in insurance_hands_list]


def find_placed_insurance(insurance_hands_list: list[str], hands_dict: dict):
    """
    Find total insurance placed for each hand. Placed insurance is half initial chips.

    Parameters:
        insurance_hands_list (list[str]): list of hands that have insurance.
        hands_dict (dict): dictionary of hands.

    Returns:
        int: total insurance placed.
    """
    if len(insurance_hands_list) == 0:
        return 0  # If list is empty, return 0 as insurance amount.
    return sum(hands_dict[head_ordinal].initial_chips for head_ordinal in insurance_hands_list) // 2


def find_value_color(value: int, soft: bool, bust: bool):
    """
    Find corresponding color of hand value.

    Parameters:
        value (int): value of given hand.
        soft (bool): if given hand is soft.
        bust (bool): if given hand is busted.

    Returns:
        str: color corresponding to hand value.
    """
    if bust:
        return VALUES_COLORS['busted']
    if (soft is False) & (DANGER_ZONE['lower'] <= value <= DANGER_ZONE['upper']):
        return VALUES_COLORS['danger']  # Value color for hard values in danger zone.
    return VALUES_COLORS['safe']


def find_total_bets(hands_dict: dict, insurance_hands_list: list[str]):
    """
    Find total bets placed in each round.

    Parameters:
        hands_dict (dict): dictionary of hands.
        insurance_hands_list (list[str]): list of hands that have insurance.

    Returns:
        int: total bets placed.
    """
    # 1st term: sum bets from each head hand's branches, then sum again along all head hands.
    total_bets = sum(sum(hands_dict[hand].chips_dict.values()) for hand in hands_dict.keys())
    # 2nd term: sum all placed insurance (50% initial chips) for each hand of insurance hands list.
    total_insurances = sum(hands_dict[hand].initial_chips for hand in insurance_hands_list) // 2
    return total_bets + total_insurances
