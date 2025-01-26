"""

UCL -- Institute of Finance & Technology
Author  : Luca Cocconcelli
Lecture : 2025-01-26
Topic   : RandomTradeGenerator

"""
import random
from datetime import datetime, timedelta
import time

from modules.data_models.trade_model import Trade

class GenerateTrades:
    """
    RandomTradeGenerator
    ====================
    
    Notes
    -----

    Class to simulate random trades

    Arguments
    ---------
        :param conf a list containing the simulation parameters
        :param input_data a list of dictionaries with bond prices from sql

    Methods
    -------
        create_one_trade creates a single random trade

    """
    def __init__(self, conf, input_data):
        self.traders = conf['TradesParameters']['tradersIds']
        self.c_tpt = conf['TradesParameters']['counterParty']
        self.quantities = conf['TradesParameters']['tradeQuantity']
        self.input_data = input_data

    def _get_random_config(self):
        trader = random.choice(self.traders)
        c_party = random.choice(self.c_tpt)
        quant = random.choice(self.quantities)
        return {'trader': trader, 'counterparty': c_party, 'quantity': quant}
    
    def _get_random_instrument(self):
        list_ceiling = len(self.input_data) - 1
        selector = random.randint(0, list_ceiling)
        return self.input_data[selector]
        
    def _get_trade_time(self):
        
        timestamp_date = datetime.strftime(self.input_data[0]['cob_date'], "%Y-%m-%dT%H:%M:%S")
        date_to_random = datetime.strptime(timestamp_date, "%Y-%m-%dT%H:%M:%S")        
        randomised_datetime = date_to_random + timedelta(seconds=random.randint(27000, 57000))
        
        random_timestamp = datetime.strftime(randomised_datetime, "%Y-%m-%dT%H:%M:%S.000Z")
        formatted_timestamp = datetime.strftime(randomised_datetime, "%Y%m%d%H%M%S")
        
        return {'rtmstmp': random_timestamp, 'frmtmstp': formatted_timestamp}
    
    def create_one_trade(self):
        random_conf = self._get_random_config()
        random_instrument = self._get_random_instrument()
        random_time = self._get_trade_time()

        buy_sell = 'SELL' if random_conf['quantity'] < 0 else 'BUY'
        bs_short = 'S' if random_conf['quantity'] < 0 else 'B'
        
        random_price = float(random_instrument['close_price']) + random.uniform(-1.5, 1.5)
        notional = random_price * float(random_conf['quantity'])
        
        trader_id = '{}{}{}{}'.format(
            bs_short,
            random_conf['trader'],
            random_instrument['symbol_id'],
            random_time['frmtmstp']
        )
        
        return Trade(DateTime = random_time['rtmstmp'], 
                    TradeId = trader_id, 
                    Trader = random_conf['trader'],
                    Symbol = random_instrument['symbol_id'],
                    Quantity = random_conf['quantity'],
                    Notional = notional,
                    TradeType = buy_sell,
                    Ccy = random_instrument["currency"],
                    Counterparty = random_conf['counterparty'])



