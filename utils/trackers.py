from configs.rules_config import CARD_TO_VALUE_DICT, MAX_TOTAL_VALUE, MIN_DEALER_VALUE


def update_properties(cards_list: list[str]):
    """
    Update properties of a hand based on given list of cards.

    Args:
        cards_list (list[str]): list of cards in given hand.

    Returns:
        tuple: tuple of hand value, a boolean telling if hand is soft, and a boolean telling if hand is busted.
    """
    soft = False
    value = sum([CARD_TO_VALUE_DICT[cards] for cards in cards_list])

    if "A" in cards_list:
        value -= 10 * cards_list.count("A")  # Count all Aces as 1 for each first.
        if value + 10 <= MAX_TOTAL_VALUE:  # Given hand is soft if an Ace can count as 11 without bust.
            value += 10  # Take the greatest possible total value.
            soft = True

    bust = True if value > MAX_TOTAL_VALUE else False
    return value, soft, bust


def track_display_value(
    value: int,
    blackjack: bool = False,
    dealer: bool = False,
    check_bj_only: bool = False,
    stand: bool = False,
    soft: bool = False,
    bust: bool = False,
):
    """
    Track hand value to be displayed on game page.

    Args:
        value (int): value of the hand.
        blackjack (bool, optional): if given hand is Blackjack. Defaults to False.
        dealer (bool, optional): if this function is called for dealer's hand. Defaults to False.
        check_bj_only (bool, optional): if dealer only needs to check whether it has Blackjack. Defaults to False.
        stand (bool, optional): if given hand has already stood. Defaults to False.
        soft (bool, optional): if given hand is soft. Defaults to False.
        bust (bool, optional): if given hand is busted. Defaults to False.

    Returns:
        str: hand value to be displayed on game page.
    """
    if blackjack:
        return "Blackjack"
    if dealer & check_bj_only:
        return "No Blackjack"
    if bust:
        return "Busted"

    # Show both possible values in either case.
    # 1. Player's soft hand hasn't stood, and is under 21.
    if (dealer is False) & soft & (stand is False) & (value < MAX_TOTAL_VALUE):
        return "/".join([str(value), str(value - 10)])

    # 2. Dealer's soft hand is under required value.
    if dealer & soft & (value < MIN_DEALER_VALUE):
        return "/".join([str(value), str(value - 10)])

    return str(value)
