"""All home configurations."""
import os
from configs.paths_config import APP_BASE_PATH
from configs.rules_config import MIN_BET, MAX_CAPITAL


DEFAULT_PLAYER_NAME = "💸Benji Bucket🪣"  # If player doesn't enter name.


HOME_CONFIG = {
    "title": "🎰JOB's Here",

    "name": "♠️♥️Jack's Online Blackjack♦️♣️",

    "intro_button": {
        "label": "🎠Intro Page🎙️",
        "url": "https://github.com/StarsExpress/Blackjack-Monkey-Intro"
    },

    "rules_button": {
        "label": "👀Read Rules📖",
        "title": "Blackjack Rules (Click anywhere to close~)",  # Title for the popup.
        "language": [  # List of buttons to show rules in supported languages.
            {
                "label": "🇺🇸English"
            },
            {
                "label": "🇹🇼繁體中文",
            },
            {
                "label": "🇨🇳简体中文",
            },
        ],
        "paths": {
            "english": os.path.join(APP_BASE_PATH, "rules", "english.txt"),
            "traditional": os.path.join(APP_BASE_PATH, "rules", "traditional.txt"),
            "simplified": os.path.join(APP_BASE_PATH, "rules", "simplified.txt")
        }
    },

    "income_button": {
        "label": "💰Income Statement📃",
        "title": "Income Statement (Click anywhere to close~)",  # Title for the popup.
        "columns": {
            "round": "Round", "profit": "Profit", "capital": "Cumulated Capital"
        }
    },

    "player_name_input": {
        "label": "😃How may we call you, Sir/Madame:",
        "holder": f"Would like to know your name, or we'll call you {DEFAULT_PLAYER_NAME}"
    },

    "capital_input": {
        "label": "💰Cash in your capital, please:",
        "holder": f"Please be integer. Available range: {str(MIN_BET)} to {str(MAX_CAPITAL)}."
    }
}
