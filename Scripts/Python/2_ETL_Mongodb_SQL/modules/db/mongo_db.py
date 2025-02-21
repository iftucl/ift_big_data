"""

UCL -- Institute of Finance & Technology
Author  : Luca Cocconcelli
Lecture : 2022-11-19
Topic   : mongo_db.py
Project : MongoDB Trades aggregator
Desc    : Class to aggregate data from MongoDB


"""
from pymongo import MongoClient
import datetime

class GetMongo:

    """
    Arguments:
        mongo_config (list): configuration for MongoDB. in ./properties/conf.yaml
        business_date (date): business date date for trade aggregation

    Public methods:
        aggregate_mongo_data: gets all trades for given business date and perform
                              aggregation by trader and isin.

    mongo_client = GetMongo(conf['dev']['config']['Database']['Mongo'],
                            datetime.datetime.strptime('2017-07-21', '%Y-%m-%d'))

    test_one = mongo_client.aggregate_mongo_data()

    
    """

    def __init__(self, mongo_config, business_date):
        self.mongo_config = mongo_config
        self.business_date = business_date

    
    def _init_mongo_client(self):
        """
        
        creates MongoDB client and points to a specific collection.
        
        """
        mng_client = MongoClient(self.mongo_config['url'])
        mng_db = mng_client[self.mongo_config['Db']]        
        mng_collection = mng_db[self.mongo_config['Collection']]
        return mng_collection

    def _create_mongo_pipeline(self):
        """
        aggregation pipeline:
            - filter only today's trades;
            - aggregate by trader & isin;
            - summarise net_quantity and net_amount as sum of quantity and notional at trade level
        """
        
        start_date = self.business_date
        end_date = self.business_date + datetime.timedelta(hours=24)
        
        pipeline = [
            {'$match': 
                {
                '$and': [{'DateTime': {'$gte': start_date}},
				        {'DateTime': {'$lt': end_date}}]
                }
            },
            {'$group': {
                '_id': 
                    {
                    'Trader': "$Trader",
                    'Symbol': '$Symbol'
                    }, 
				'NetNotional': {'$sum': "$Notional"},
				'NetQuantity':  {'$sum': "$Quantity"}
                } 
            }
        ]        
        return pipeline

    def _aggregate_mongo_data(self): 
        
        pipe_line = self._create_mongo_pipeline()

        client_collection = self._init_mongo_client()
        # this will return a MongoDB cursor in result
        cursor = client_collection.aggregate(pipeline=pipe_line)
        # now convert cursor to list
        results = list(cursor)
        return results

    def aggregate_to_load(self):
        
        bus_date = datetime.datetime.strftime(self.business_date, '%Y-%m-%d')
        data_load = self._aggregate_mongo_data()
        
        list_output = []
        
        for dict in data_load:
            date_id = bus_date.replace('-', '') + dict['_id']['Trader'] + dict['_id']['Symbol']
            list_output.append({
                'cob_date': bus_date,
                'pos_id': date_id,
                'trader': dict['_id']['Trader'], 
                'symbol': dict['_id']['Symbol'], 
                'ccy': 'GBP',
                'net_amount': dict['NetNotional'],
                'net_quantity': dict['NetQuantity']
                })     
        return list_output
   
