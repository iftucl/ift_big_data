"""

UCL -- Institute of Finance & Technology
Author  : Luca Cocconcelli
Lecture : 2024-02-21
Topic   : Main.py
Project : SQL Trades aggregator & uploader

"""

import datetime
import time


from modules.utils.info_logger import print_info_log
from modules.utils.args_parser import arg_parse_cmd
from modules.utils.config_parser import Config
from modules.db.mongo_db import GetMongo
from modules.db.sql_conn import DatabaseMethods


sql_table = 'cash_equity.portfolio_positions'

if __name__ == '__main__':
    print_info_log('Script started', 'progress')
    
    args = arg_parse_cmd()
    parsed_args = args.parse_args()
        
    conf = Config('dev') #parsed_args.environment

    print_info_log('Command line argument parsed & main config loaded', 'progress')
    # date_run = datetime.datetime.strptime('2016-07-01', '%Y-%m-%d')
    mongo_data = GetMongo(mongo_config=conf['config']['Database']['Mongo'],business_date=date_run) #
    # we aggregate trades
    aggregates_trades = mongo_data.aggregate_to_load()
        
    database_client = DatabaseMethods(conf['config']['Database']['Postgres'], 'Postgres')
    
    database_client.execute(None, 'upsert', aggregates_trades)
    print_info_log('Trades aggregation and upsert completed', 'progress')
