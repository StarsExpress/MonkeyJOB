from pywebio.output import put_table, put_html
from configs.output_config import PROFIT_TABLE_CSS, PLAYER_SCOPE, PLAYER_SUB_SCOPES, PROFITS_COLORS, TABLE_HEADERS
from configs.rules_config import BLACKJACK_PAY, INSURANCE_PAY
from widgets.layouts import clear_contents, write_text


def return_chips(
        head_ordinal: str,
        branch_ordinal: str = "1",
        chips: int = 0,
        surrender: bool = False,
        early_pay: bool = False,
        insurance: int = 0,
        player_bj: bool = False,
        dealer_bj: bool = False,
        player_bust: bool = False,
        player_value: int = 0,
        dealer_value: int = 0,
):
    """
    Display profit of input hand, and return chips.

    Args:
        head_ordinal (str): ordinal of head.
        branch_ordinal (str, optional): ordinal of branch. Defaults to "1".
        chips (int, optional): final bets placed at input hand. Defaults to 0.
        surrender (bool, optional): if player surrenders. Defaults to False.
        early_pay (bool, optional): if player opts for Blackjack early pay. Defaults to False.
        insurance (int, optional): 1 = player wins insurance; -1 = player loses insurance; 0 otherwise. Defaults to 0.
        player_bj (bool, optional): if player has Blackjack. Defaults to False.
        dealer_bj (bool, optional): if dealer has Blackjack. Defaults to False.
        player_bust (bool, optional): if player's hand is busted. Defaults to False.
        player_value (int, optional): value of player's hand. Defaults to 0.
        dealer_value (int, optional): value of dealer's hand. 0 = dealer is busted. Defaults to 0.

    Returns:
        int: number of chips returned to player.
    """
    put_html(PROFIT_TABLE_CSS)  # Control profit table width.

    branch_scope = f"{PLAYER_SCOPE}_{head_ordinal}_{branch_ordinal}"  # Branch and profit scopes for input hand.
    profit_scope = f"{branch_scope}_{PLAYER_SUB_SCOPES['profit']}"
    clear_contents(profit_scope)  # Erase old value for new value.

    if surrender:  # Player loses 50% of chips.
        put_table(
            [[-chips // 2]], header=TABLE_HEADERS["profit"], scope=profit_scope
        ).style(f"color:{PROFITS_COLORS['loss']}")

        write_text("You surrender and lose 50%.", branch_scope, False)
        return chips // 2

    if player_bj & early_pay:  # Profit = chips if player opts for Blackjack early pay.
        put_table(
            [[chips]], header=TABLE_HEADERS["profit"], scope=profit_scope
        ).style(f"color:{PROFITS_COLORS['profit']}")

        write_text("You take early pay on Blackjack.", branch_scope, False)
        return chips * 2

    ins_term = (chips // 2) * INSURANCE_PAY if insurance == 1 else (0 if insurance == 0 else -chips // 2)
    ins_message = '\nInsurance wins.' if insurance == 1 else ('' if insurance == 0 else '\nInsurance loses.')
    ins_chips = (chips // 2) * (1 + INSURANCE_PAY) if insurance == 1 else 0

    if player_bust:  # Player loses all chips.
        profit = ins_term - chips
        style = PROFITS_COLORS["loss"] if profit < 0 else PROFITS_COLORS["tie"]
        put_table(
            [[profit]], header=TABLE_HEADERS["profit"], scope=profit_scope
        ).style(f"color:{style}")

        bust_message = "Your hand is busted." if insurance == 0 else ""
        write_text(f"{bust_message}{ins_message}", branch_scope, False)
        return ins_chips

    if dealer_bj:  # If dealer has Blackjack.
        if player_bj:
            put_table(
                [[0]], header=TABLE_HEADERS["profit"], scope=profit_scope
            ).style(f"color:{PROFITS_COLORS['tie']}")

            write_text("Dealer and you both have Blackjack.", branch_scope, False)
            return chips

        profit = ins_term - chips
        style = PROFITS_COLORS["loss"] if profit < 0 else PROFITS_COLORS["tie"]
        put_table([[profit]], header=TABLE_HEADERS["profit"], scope=profit_scope).style(
            f"color:{style}"
        )

        write_text(f"Dealer has Blackjack and you don't.{ins_message}", branch_scope, False)
        return ins_chips

    if player_bj:  # Blackjack profit = chips * preset payout rate.
        put_table(
            [[int(chips * BLACKJACK_PAY)]],
            header=TABLE_HEADERS["profit"],
            scope=profit_scope,
        ).style(f"color:{PROFITS_COLORS['profit']}")

        write_text("You have Blackjack and dealer doesn't.", branch_scope, False)
        return int(chips * (1 + BLACKJACK_PAY))

    if player_value < dealer_value:
        put_table(
            [[ins_term - chips]],
            header=TABLE_HEADERS["profit"],
            scope=profit_scope,
        ).style(f"color:{PROFITS_COLORS['loss']}")

        write_text(f"Dealer's value > your value.{ins_message}", branch_scope, False)
        return 0

    if player_value == dealer_value:
        style = PROFITS_COLORS['loss'] if ins_term < 0 else PROFITS_COLORS['tie']
        put_table(
            [[ins_term]], header=TABLE_HEADERS["profit"], scope=profit_scope
        ).style(f"color:{style}")

        write_text(f"You and dealer are tied.{ins_message}", branch_scope, False)
        return chips

    put_table(
        [[chips + ins_term]],
        header=TABLE_HEADERS["profit"],
        scope=profit_scope,
    ).style(f"color:{PROFITS_COLORS['profit']}")

    reason = "Dealer is busted but you aren't." if dealer_value == 0 else "Your value > dealer's value."
    write_text(f"{reason}{ins_message}", branch_scope, False)
    return chips * 2
