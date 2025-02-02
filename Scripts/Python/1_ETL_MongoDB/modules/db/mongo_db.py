"""

UCL -- Institute of Finance & Technology
Author  : Luca Cocconcelli
Lecture : 2024-02-22
Topic   : Main.py
Project : MongoDB Trades uploader
Desc    : Class to load data into MongoDB


"""
from ift_global import MinioFileSystemRepo
from pymongo import MongoClient
from datetime import datetime

from modules.input.read_file import ReadInputFiles

class LoadMongo(ReadInputFiles):

    def __init__(self, mongo_config, file_config, log_file):
        self.mongo_config = mongo_config
        super().__init__(file_config, log_file)

    def _format_mongo_fields(self, mongo_dictionary):

        for mongo_entry in mongo_dictionary:
            mongo_entry['DateTime'] = datetime.strptime(mongo_entry['DateTime'], '%Y-%m-%d %H:%M:%S%z')
            mongo_entry['Quantity'] = float(mongo_entry['Quantity'])
            mongo_entry['Notional'] = float(mongo_entry['Notional'])
        
        return mongo_dictionary
    
    def _init_mongo_client(self):
        mng_client = MongoClient(self.mongo_config['url'])
        mng_db = mng_client[self.mongo_config['Db']]
        mng_collection = mng_db[self.mongo_config['Collection']]
        return mng_collection

    def load_mongo_data(self):
        #get_trades = ReadInputFiles
        #file_name = get_trades.get_latest_input_file(self)
        data_load_noformat = self.read_dictionary()

        if not data_load_noformat:
            return None

        data_load = self._format_mongo_fields(data_load_noformat)

        client_collection = self._init_mongo_client()        
        response = client_collection.insert_many(data_load)

        if response.acknowledged:
            self._write_log_file(self.file_name)
        return response.acknowledged
