"""All bets configurations."""

MAX_CAPITAL = 10000000

MAX_BET = 10000
MIN_BET = 300

BLACKJACK_PAY = 1.5

# Whole-round ROI congrats popup (ported from v1.0.0 POPUP_DICT["huge_profits"]).
# Fires once after a round is fully settled, when the round's net profit divided
# by the total chips committed (base bets + double/split wagers + insurance)
# meets this ratio. 0.7 == a 70% return on everything staked that round.
HUGE_PROFIT_RATIO = 0.7
