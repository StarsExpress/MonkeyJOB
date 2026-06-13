from pywebio.output import put_button
from pywebio.session import run_js
from configs.output_config import INTRO_SUB_SCOPES


def redirect_to_intro_page():
    """Handle button click and redirection. "_blank" opens another tab."""
    run_js(f"""window.open("{INTRO_SUB_SCOPES['url']}", "_blank");""")


def show_intro():
    """Display a button that redirects to GitHub intro page."""
    put_button(
        label=INTRO_SUB_SCOPES["label"],
        color=INTRO_SUB_SCOPES["color"],
        onclick=redirect_to_intro_page,
        scope=INTRO_SUB_SCOPES["intro"],
    )
