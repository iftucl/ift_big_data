"""

UCL -- Institute of Finance & Technology
Author  : Luca Cocconcelli
Lecture : 2025-01-31
Topic   : Main.py
Project : Random Trade Generator

"""

from ift_global import ReadConfig
from ift_global.utils.set_env_var import set_env_variables

# Import local modules
from modules.utils.info_logger import trades_logger
from modules.utils.args_parser import arg_parse_cmd
from modules.input.db_connection import DataBaseConnect
from modules.trades.RandomTradeGenerator import GenerateTrades
from modules.output.write_output import WriteOutputFile

if __name__ == '__main__':
    trades_logger.info("Script started")
    args = arg_parse_cmd()
    parsed_args = args.parse_args()
    # source config, env_type = 'dev'; cfg = ReadConfig("dev")    
    trades_logger.info("Read config from yaml file")
    # example: cfg = ReadConfig("dev")
    cfg = ReadConfig(parsed_args.env_type)
    
    set_env_variables(env_variables=cfg['config']['env_variables'],
                      env_type=parsed_args.env_type,
                      env_file=True)
    # set_env_variables(env_variables=cfg['config']['env_variables'], env_type="dev", env_file=True)

    trades_logger.info('Command line argument parsed & main config loaded')

    if not parsed_args.simulation_number:
        total_simulation = cfg['params']['TradesParameters']['SimulationNumber']
        trades_logger.info('Total number of simulation defaulted to yaml config')
    else:
        total_simulation = parsed_args.simulation_number
    # establish connection to database; as example: from datetime import datetime; date_run = datetime.strptime('2023-11-23', '%Y-%m-%d')
    # conn = DataBaseConnect(sql_config=cfg['config']['Database']["Postgres"], db_type =  "Postgres")
    conn = DataBaseConnect(cfg['config']['Database'][parsed_args.input_database], db_type =  parsed_args.input_database)
    # get prices, as example you can use 2023-11-23 as:
    # equity_prices = conn.get_data_query("SELECT * FROM cash_equity.equity_prices WHERE cob_date = '{}'".format(date_run))
    equity_prices = conn.get_data_query("SELECT * FROM cash_equity.equity_prices WHERE cob_date = '{}'".format(parsed_args.date_run))
    conn.close_conn()
    
    trades_logger.info('SQL Info loaded')
    
    #-init trade object
    trades_logger.info("Trades simulation starts")
    random_trader = GenerateTrades(conf=cfg['params'], input_data=equity_prices)
    # simulate some trades, total_simulation = 5
    trade_simul = []
    for i in range(1, total_simulation):
        trade_simul.append(random_trader.create_one_trade())

    #-- write output
    trades_logger.info(f"Trades simulation Completed, writing {parsed_args.output_file} output")    
    write_output = WriteOutputFile(cfg['params']['OutputFile'], parsed_args.output_file)
    # write_output = WriteOutputFile(cfg['params']['OutputFile'], "csv")
    write_output.write_output_minio(trade_simul, file_type="csv")
    trades_logger.info('Script successfully completed')
