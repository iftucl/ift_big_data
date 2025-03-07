import argparse

def arg_parse_cmd():
    parser = argparse.ArgumentParser(
        description = 'MongoDB Data Loader'
    )
    parser.add_argument(
        '--repo_directory',
        required=False,
        help='Provide repository home directory'
    )
    parser.add_argument(
        '--date_run',
        required=False,
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