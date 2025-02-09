import datetime
import argparse

def arg_parse_cmd():
    parser = argparse.ArgumentParser(
        description = 'MongoDB Data Loader'
    )
    parser.add_argument(
        '--environment',
        type=str,
        required=False,
        choices=['dev','docker'],
        help='Name of the environment on which you would like to run the code'
    )
    parser.add_argument(
        '--repo_directory',
        required=False,
        help='Provide repository home directory'
    )
    parser.add_argument(
        '--date_run',
        required=True,
        help='Provide date to run in format YYYY-MM-DD',
        type=lambda d: datetime.datetime.strptime(d, '%Y-%m-%d')
    )
    return parser