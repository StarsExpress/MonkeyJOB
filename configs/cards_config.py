"""All cards configurations."""

CARDS_LIST = ([str(card) for card in range(2, 11)] + ["J", "Q", "K", "A"]) * 4

# Dictionary to map card name and value.
CARD_TO_VALUE_DICT = dict(
    zip(
        CARDS_LIST, [card for card in range(2, 11)] + [10, 10, 10, 11]
    )
)

NUMBER_OF_DECKS = 6

SUITS = ["S", "H", "D", "C"]  # S: spade; H: heart; D: diamond; C: club.
SUITS_DICT = {
    key: SUITS * NUMBER_OF_DECKS
    for key in [str(card) for card in range(2, 11)] + ["J", "Q", "K", "A"]
}
