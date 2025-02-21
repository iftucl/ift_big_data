"""

UCL -- Institute of Finance & Technology
Author  : Luca Cocconcelli
Lecture : 2024-02-21
Topic   : Main.py
Project : SQL Trades aggregator & uploader

"""

from ift_global import ReadConfig
from ift_global.utils.set_env_var import set_env_variables

import datetime
import time


from modules.utils.info_logger import etl_postgres_logger
from modules.utils.args_parser import arg_parse_cmd
from modules.db.mongo_db import GetMongo
from modules.db.sql_conn import DatabaseMethods


sql_table = 'cash_equity.portfolio_positions'

if __name__ == '__main__':
    etl_postgres_logger.info('MongoDB to SQL ETL - Script started')


    args = arg_parse_cmd()
    parsed_args = args.parse_args()
        
    # example: conf = ReadConfig("dev")
    conf = ReadConfig(parsed_args.env_type)
    
    set_env_variables(env_variables=conf['config']['env_variables'],
                      env_type=parsed_args.env_type,
                      env_file=True)
    # set_env_variables(env_variables=conf['config']['env_variables'], env_type="dev", env_file=True)
    etl_postgres_logger.info('Command line argument parsed & main config loaded')
    # date_run = datetime.datetime.(2023, 11, 23)
    date_run = parsed_args.date_run
    etl_postgres_logger.info('Establish client connection to MongoDB')
    mongo_data = GetMongo(mongo_config=conf['config']['Database']['Mongo'],business_date=date_run) #
    # we aggregate trades on Mongodb server side
    etl_postgres_logger.info('Aggregate and Fetch Trades Data from MongoDB')
    aggregated_trades = mongo_data.aggregate_to_load()
    # gets postgresql connection
    etl_postgres_logger.info('MongoDB data retrieved. Opening Client to Postgresql.')
    database_client = DatabaseMethods(conf['config']['Database']['Postgres'], 'Postgres')
    etl_postgres_logger.info(f'Client postgres connection established')
    # upsert trades
    database_client.execute(ops_type='upsert', data_load=aggregated_trades)
    etl_postgres_logger.info('Trades aggregation and upsert completed')
