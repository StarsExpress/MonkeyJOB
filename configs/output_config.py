"""All output configurations."""

TITLE_SCOPE = "Title"
PAGE_WIDTH = "100%"
IMAGES_WIDTH = "60px"


# Sub scopes within intro scope.
INTRO_SUB_SCOPES = {
    "intro": "intro",
    "button": "intro_button",
    "label": "🎠Intro Page🎙️",
    "color": "info",
    "url": "https://github.com/StarsExpress/Blackjack-Monkey-Intro",
}

# Sub scopes within rules scope.
RULES_SUB_SCOPES = {
    "rules": "rules",
    "buttons": "rules_buttons",
    "content": "rules_content",
}

# Sub scopes within income scope.
INCOME_SUB_SCOPES = {
    "income": "income",
    "content": "income_content",
    "columns": ["Round", "Profit", "Cumulated Capital"],
}


INFO_SCOPE = "Info"  # Scope of player info.
CAPITAL_TEXT = ": your cumulated capital is "  # Capital tracking.


# Scope of player's each hand.
PLAYER_HEADER = "Your Hands"
PLAYER_SCOPE = "Player"

# Sub scopes within player scope.
PLAYER_SUB_SCOPES = {
    "chips": "Chips",
    "cards": "Cards",
    "value": "Value",
    "profit": "Profit",
}

# Headers for tables of chips, value and profit.
TABLE_HEADERS = {
    "chips": ["Bet", "Insurance"],
    "value": ["Value"],
    "profit": ["Profit"],
}

# Control profit table width.
PROFIT_TABLE_CSS = """
    <style>
    .custom-table {
        width: 400px;
    }
    </style>
    """


# Scope of dealer's hand.
DEALER_HEADER = "Dealer's Hand"
DEALER_SCOPE = "Dealer"

# Sub scopes within dealer scope.
DEALER_SUB_SCOPES = {
    "cards": f"{DEALER_SCOPE}_Card",
    "value": f"{DEALER_SCOPE}_Value",
}

SHARED_HEIGHT = 350  # Shared by player & dealer scopes.
RELATIVE_WIDTH = "65% 35px 35%"  # Player scope, middle blank and dealer scope.


# Hands values style.
VALUES_COLORS = {"safe": "black", "danger": "orange", "busted": "red"}
DANGER_ZONE = {"lower": 12, "upper": 16}

# Profits style.
PROFITS_COLORS = {"loss": "red", "tie": "black", "profit": "green"}

# Notifications widget.
POPUP_DICT = {
    "inadequate_capital": {"title": "‼️Inadequate Capital‼️"},
    "max_splits": {"title": "⛔No More Splits⛔"},
    "early_exit": {"title": "🛬Early Exit🛬", "content": "Your hands are all judged."},
    "huge_profits": {
        "title": "🎉Winner Winner Chicken Dinner🦃",
        "emojis": ("💵", "🍾"),
        "threshold": 0.7,
    },
}
POPUP_IMPLICIT_CLOSE = "\n(Click anywhere to close~)"  # Reminder of how to close popup.
POPUP_SIZE = 5
