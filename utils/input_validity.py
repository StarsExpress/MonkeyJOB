from configs.input_config import MAX_NAME_LEN
from configs.rules_config import MIN_BET, MAX_CAPITAL


def check_name(name: str):
    """
    Check if player's name length, after removal of edge spaces, is within defined limit.

    Args:
        name (str): player's name.

    Returns:
        str: an error message if name length is over defined limit, None otherwise.
    """
    if len(name.lstrip().rstrip()) > MAX_NAME_LEN:
        return f'Name length must <= {str(MAX_NAME_LEN)}.'


def check_capital(capital: int):
    """
    Check if player's initial capital is within defined range.

    Args:
        capital (int): player's initial capital.

    Returns:
        str: an error message if capital is out of defined range, None otherwise.
    """
    if capital < MIN_BET:
        return f'Capital must >= minimum bet {str(MIN_BET)}.'
    if capital > MAX_CAPITAL:
        return f'Capital must <= maximum capital {str(MAX_CAPITAL)}.'
