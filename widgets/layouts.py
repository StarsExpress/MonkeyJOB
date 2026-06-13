from pywebio.platform import config
from pywebio.session import set_env
from pywebio.output import put_html, put_collapse, put_scrollable, put_scope
from pywebio.output import put_row, put_text, put_tabs, clear, use_scope
from configs.app_config import PAGE_NAME, PAGE_THEME, PAGE_TITLE
from configs.output_config import TITLE_SCOPE, PLAYER_HEADER, PLAYER_SCOPE, DEALER_HEADER, DEALER_SCOPE, PAGE_WIDTH
from configs.output_config import INTRO_SUB_SCOPES, RULES_SUB_SCOPES, INCOME_SUB_SCOPES, SHARED_HEIGHT, RELATIVE_WIDTH


def set_name_and_theme():
    """Set name and theme of game page."""
    config(title=PAGE_NAME, theme=PAGE_THEME)


def set_top_layouts():
    """Set page title and sub scopes for intro, rules and income."""
    put_scope(
        name=TITLE_SCOPE,
        content=put_html(
            f"""<h1 align='center'><strong>{PAGE_TITLE}</strong></h1>""",
            scope=TITLE_SCOPE,
        ),
    )
    put_row(
        content=[
            put_scope(INTRO_SUB_SCOPES["intro"]),
            put_scope(RULES_SUB_SCOPES["rules"]),
            put_scope(INCOME_SUB_SCOPES["income"]),
        ],
        scope=TITLE_SCOPE,
    )


def set_core_layouts_width():
    """Set core layouts' width w.r.t. page width in config."""
    set_env(output_max_width=PAGE_WIDTH)


def set_core_layouts():
    """Set game page layouts: two parallel contents."""
    player_content = put_collapse(  # Left side content: scope for cards of each player's hand.
        PLAYER_HEADER,
        put_scrollable(put_scope(PLAYER_SCOPE), height=SHARED_HEIGHT, keep_bottom=True),
        open=True,
    )
    dealer_content = put_collapse(  # Right side content: scope for dealer's cards.
        DEALER_HEADER,
        put_scrollable(put_scope(DEALER_SCOPE), height=SHARED_HEIGHT, keep_bottom=True),
        open=True,
    )
    put_row([player_content, None, dealer_content], size=RELATIVE_WIDTH)  # None: middle blank between scopes.


def set_cards_tabs(head_hands: int):
    """Set tabs to store scopes for each head hand and its branches."""
    tabs = []
    for i in range(1, head_hands + 1):
        head_scope = f"{PLAYER_SCOPE}_{str(i)}"
        content = put_scope(
            name=head_scope,
            content=put_text(f"Hand {str(i)}'s Branches", scope=head_scope),
        )
        tabs.append({"title": f"Hand {str(i)}", "content": content})

    put_tabs(tabs, PLAYER_SCOPE)


def clear_contents(scopes: list[str] | str):
    """Clear contents inside given scope(s)."""
    if isinstance(scopes, list):
        for scope in scopes:
            clear(scope)

    else:
        clear(scopes)


def write_text(message: str, scope: str, clear_scope: bool = True):
    """
    Performs put_text in given scope.

    Args:
        message (str): message to put.
        scope (str): scope to put message in.
        clear_scope (bool, optional): whether to clear scope before putting message. Defaults to True.
    """
    with use_scope(scope, clear=clear_scope) as s:
        put_text(message, scope=s)
