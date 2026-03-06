import argparse
from datetime import datetime

def valid_date(d):
    """
    Validate input and serialise to datetime.

    :param d: a string with conventions 'YYYY-MM-DD'
    :type d: str

    :return: a valid datetime object
    :rtype: datetime

    :Examples:
        >>> from modules.utils.args_parser import valid_date
        >>> valid_date("2026-01-01")
        datetime(2026, 1, 1)
    """
    if not d:
        return datetime.now()
    
    try:
        user_date = datetime.strptime(d, "%Y-%m-%d")
        return user_date
    except ValueError:
        cmd_error = f"date_run argument provided {d} is in incorrect format. Please, provide YYYY-MM-DD"
        raise argparse.ArgumentTypeError(cmd_error)

def arg_parse_cmd():
    parser = argparse.ArgumentParser(
        description = 'Postgresql Data Loader using Duckdb'
    )
    parser.add_argument(
        '--repo_directory',
        required=False,
        help='Provide repository home directory'
    )
    parser.add_argument(
        '--run_date',
        required=False,
        type=valid_date,
        default="",
        help='Provide date to run in format YYYY-MM-DD'
    )
    parser.add_argument(
        '--env_type',
        required=True,
        choices=['dev', 'docker'],        
        type=str,
        help='Provide environment type: dev or docker where dev is your local machine.'
    )
    return parser