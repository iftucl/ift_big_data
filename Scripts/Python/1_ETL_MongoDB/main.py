"""

UCL -- Institute of Finance & Technology
Author  : Luca Cocconcelli
Lecture : 2024-02-02
Topic   : Main.py
Project : MongoDB Trades uploader

"""
from ift_global import ReadConfig
from ift_global.utils.set_env_var import set_env_variables

import os

from modules.utils.info_logger import etl_mongo_logger
from modules.utils.args_parser import arg_parse_cmd
from modules.utils.config_parser import Config
from modules.db.mongo_db import LoadMongo


if __name__ == '__main__':
    etl_mongo_logger.info('Script started')
    
    args = arg_parse_cmd()
    parsed_args = args.parse_args()    

    # example: conf = ReadConfig("dev")
    conf = ReadConfig(parsed_args.env_type)
    
    set_env_variables(env_variables=conf['config']['env_variables'],
                      env_type=parsed_args.env_type,
                      env_file=True)
    # set_env_variables(env_variables=conf['config']['env_variables'], env_type="dev", env_file=True)

    etl_mongo_logger.info('Command line argument parsed & main config loaded')
    mongo_loader = LoadMongo(mongo_config=conf['config']['Database']['Mongo'],
                             file_config=conf['params']['OutputFile'],
                             log_file='./static/file_load_logger.txt')    
    mongo_loader.get_latest_input_file()
    mongo_loader.load_mongo_data()
    etl_mongo_logger.info('Script completed')    