import argparse

def arg_parse_cmd():
    parser = argparse.ArgumentParser(
        description = 'Calibrate Factors to Detect Outlyers'
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