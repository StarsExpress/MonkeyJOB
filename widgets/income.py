from pywebio.output import put_scope, put_button, popup, put_datatable
from configs.output_config import INCOME_SUB_SCOPES
from configs.input_config import INCOME_DICT


def show_income(income_list: list[dict[str, str]]):
    """
    Display income data in a popup when button is clicked.

    This function creates a button with label and color specified in INCOME_DICT.

    When button is clicked, a popup appears displaying a table of income data.

    Args:
        income_list (list[dict[str, str]]): list of dictionaries containing income data.
    """
    put_button(
        label=INCOME_DICT["label"],
        color=INCOME_DICT["color"],
        onclick=lambda: popup(
            INCOME_DICT["title"],
            put_scope(
                INCOME_SUB_SCOPES["content"],
                put_datatable(
                    records=income_list,
                    instance_id=f"{INCOME_SUB_SCOPES['content']}_table",
                    column_order=INCOME_SUB_SCOPES["columns"],
                    theme="balham",
                    scope=INCOME_SUB_SCOPES["content"],
                ),
            ),
            INCOME_DICT["size"],
            True,
        ),
        scope=INCOME_SUB_SCOPES["income"],
    )
