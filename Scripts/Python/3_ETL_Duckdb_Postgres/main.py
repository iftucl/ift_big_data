"""

UCL -- Institute of Finance & Technology
Author  : Luca Cocconcelli
Lecture : 2024-02-22
Topic   : Main.py
Project : MongoDB Trades uploader

"""
from ift_global import ReadConfig
from ift_global.utils.set_env_var import set_env_variables

import os

from modules.utils.info_logger import etl_duckdb_logger
from modules.utils.args_parser import arg_parse_cmd
from modules.input.read_file import ReadInputFiles
from modules.trades_aggregator import get_aggregated_trades
from modules.db_ops.sql_conn import DatabaseMethods


if __name__ == '__main__':
    etl_duckdb_logger.info('Duckdb aggregate script started')
    
    args = arg_parse_cmd()
    parsed_args = args.parse_args()    

    # example: conf = ReadConfig("dev")
    conf = ReadConfig(parsed_args.env_type)
    
    set_env_variables(env_variables=conf['config']['env_variables'],
                      env_type=parsed_args.env_type,
                      env_file=True)
    # set_env_variables(env_variables=conf['config']['env_variables'], env_type="dev", env_file=True)

    etl_duckdb_logger.info(f'Command line argument parsed & main config loaded')
    input_trades = ReadInputFiles(file_config=conf['params']['OutputFile'], log_file='./static/file_load_logger.txt')
    granular_trades = input_trades.read_dictionary()    
    etl_duckdb_logger.info(f'Trades read from : {input_trades.file_name}')
    aggregated_trades = get_aggregated_trades(trades_list=granular_trades)
    etl_duckdb_logger.info(f'Trades {input_trades.file_name} aggregated using duckdb.')
    database_client = DatabaseMethods(conf['config']['Database']['Postgres'], 'Postgres')
    etl_duckdb_logger.info(f'established db connection via sql client')    
    database_client.execute(ops_type='upsert', data_load=aggregated_trades)
    etl_duckdb_logger.info('Trades aggregation and upsert completed', 'progress')
    database_client.execute(sql_statement="SELECT * FROM cash_equity.portfolio_positions", ops_type="read")


    etl_duckdb_logger.info('Duckdb aggregate script completed')    