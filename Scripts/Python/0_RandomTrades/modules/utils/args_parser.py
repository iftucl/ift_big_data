"""

UCL -- Institute of Finance & Technology
Author  : Luca Cocconcelli
Lecture : 2024-02-22

"""
from datetime import datetime
import argparse

def valid_date(d):
    '''Checks date input is in valid format'''
    if len(d) == 0:
        current_dt = datetime.utcnow()
        return datetime.strftime(current_dt, '%Y-%m-%d')
    elif len(d) == 10:
        return datetime.strptime(d, '%Y-%m-%d')
    else:
        cmd_error = f'date_run provided {d} is in incorrect format. Please provide format YYYY-MM-DD.'
        raise argparse.ArgumentTypeError(cmd_error)

# argparser function
def arg_parse_cmd():
    parser = argparse.ArgumentParser(
        description = 'Random trade generator script'
    )
    parser.add_argument(
        '--env_type',
        required=True,
        choices=['dev', 'docker'],        
        type=str,
        help='Provide environment type: dev or docker where dev is your local machine.'
    )
    parser.add_argument(
        '--repo_directory',
        required=False,
        help='Provide repository home directory'
    )
    parser.add_argument(
        '--date_run',
        required=True,
        type=valid_date,
        help='Provide date to run in format YYYY-MM-DD'
    )
    parser.add_argument(
        '--simulation_number',
        required=False,
        type=int,
        help='Provide the number of trades to be generated. If null, will default to yml properties'
    )
    parser.add_argument(
        '--output_file',
        required=False,
        choices=['parquet', 'avro', 'csv'],
        default='csv',
        type=str,
        help='Provide file type for output.'
    )
    parser.add_argument(
        '--input_database',
        required=True,
        choices=['SQLite', 'Postgres'],
        default='Postgres',
        type=str,
        help='Provide database type.'
    )
    return parser