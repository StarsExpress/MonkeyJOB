from configs.rules_config import CARD_TO_VALUE_DICT, SURRENDER_TO_ACE, MAX_SPLITS


def judge_blackjack(cards_list: list[str], split: bool = False) -> bool:
    """
    Determine if a hand is Blackjack.

    Args:
        cards_list (list[str]): list of cards of given hand.
        split (bool, optional): if given hand is a split hand. Defaults to False.

    Returns:
        bool: True if given hand is Blackjack, False otherwise.
    """
    if split:  # No Blackjack if split is conducted.
        return False

    if (len(cards_list) == 2) & ('A' in cards_list) & (len({'10', 'J', 'Q', 'K'} & set(cards_list)) == 1):
        return True
    return False


def judge_surrender(cards_list: list[str], dealer_first_card: str, splits: int) -> bool:
    """
    Determine if given hand can be surrendered.

    Args:
        cards_list (list[str]): list of cards of given hand.
        dealer_first_card (str): first card of dealer's hand.
        splits (int): number of splits made.

    Returns:
        bool: True if given hand can be surrendered, False otherwise.
    """
    if (len(cards_list) == 2) & (SURRENDER_TO_ACE | (dealer_first_card != 'A')) & (splits == 0):
        return True
    return False


def judge_split(cards_list: list[str], splits: int) -> bool:
    """
    Determine if given hand can be split.

    Args:
        cards_list (list[str]): list of cards of given hand.
        splits (int): number of splits made.

    Returns:
        bool: True if given hand can be split, False otherwise.
    """
    if splits < MAX_SPLITS:
        if (len(cards_list) == 2) & (CARD_TO_VALUE_DICT[cards_list[0]] == CARD_TO_VALUE_DICT[cards_list[-1]]):
            return True
    return False
