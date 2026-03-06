"""

UCL -- Institute of Finance & Technology
Author  : Luca Cocconcelli
Lecture : 2026-03-06
Topic   : Main.py
Project : Trades aggregator using duck db.

This trade aggregator leverages on DuckDB httpfs extension to collect all files generated based on a regex expression type.
In reading all files, it performs a group by and sum by trader, symbol and currency.

"""
from ift_global import ReadConfig
from ift_global.utils.set_env_var import set_env_variables
from datetime import datetime 
import os

from modules.utils.info_logger import etl_duckdb_logger
from modules.utils.args_parser import arg_parse_cmd
from modules.db_ops import (
    DuckDBMinioReader,
    DatabaseMethods
)
from modules.trades_aggregator import get_aggregated_trades
from modules.data_models.port_position_model import PortfolioPositions

def main():
    """
    Main functionality to aggregate daily trades.
    """
    pass

if __name__ == '__main__':
    etl_duckdb_logger.info('Duckdb aggregate script started')
    
    args = arg_parse_cmd()
    parsed_args = args.parse_args()    

    # example: env_type = "dev"
    env_type=parsed_args.env_type
    conf = ReadConfig(env_type)
    
    set_env_variables(env_variables=conf['config']['env_variables'],
                      env_type=env_type,
                      env_file=True)
    # set_env_variables(env_variables=conf['config']['env_variables'], env_type="dev", env_file=True)
    etl_duckdb_logger.info(f'Command line argument parsed & main config loaded')
    # get latest file from MinIO
    duck_client = DuckDBMinioReader(
        bucket_name=conf['config']['Database']['Minio']['Bucket'],
        region="eu-west-1",
        endpoint_url="localhost:9000")
    # read latest file from MinIO
    # equivalent of -> business_date = datetime(2026, 1, 1).strftime('%Y%m%d')
    business_date = args.run_date.strftime('%Y%m%d')
    
    etl_duckdb_logger.info(f'Aggregate all Trades for : {business_date}')
    daily_aggregation = get_aggregated_trades(
        duck_client=duck_client,
        dl_path=conf['params']['OutputFile']['DataLake'],
        file_name=conf['params']['OutputFile']['FileName'],
        business_date=business_date
    )    
    # aggregate in-memory trades using DuckDB
    etl_duckdb_logger.info(f'Trades for {business_date} aggregated using duckdb.')
    # establish connection to postgres database
    database_client = DatabaseMethods(conf['config']['Database']['Postgres'], 'Postgres')
    etl_duckdb_logger.info(f'established db connection via sql client')
    # 
    aggregated_trades=[PortfolioPositions(**x) for x in daily_aggregation]
    database_client.execute(ops_type='upsert', data_load=aggregated_trades)
    etl_duckdb_logger.info('Trades aggregation and upsert completed')
    etl_duckdb_logger.info('Duckdb aggregate script completed')    