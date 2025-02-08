"""

UCL -- Institute of Finance & Technology
Author  : Luca Cocconcelli
Lecture : 2025-02-22
Topic   : mongo_db.py
Project : MongoDB Trades uploader
Desc    : Class to load data into MongoDB


"""

from pymongo import MongoClient
from datetime import datetime

from modules.utils.info_logger import etl_mongo_logger
from modules.input.read_file import ReadInputFiles

class LoadMongo(ReadInputFiles):
    """
    A class for loading data into a MongoDB.

    This class extends the `ReadInputFiles` class to read files,
    process their contents, and load the data into a MongoDB collection.    

    :param mongo_config: Configuration for connecting to MongoDB. Should include:
        - `url` (str): The MongoDB connection URL.
        - `Db` (str): The name of the database.
        - `Collection` (str): The name of the collection.
    :type mongo_config: dict
    :param file_config: Configuration for reading input files (inherited from `ReadInputFiles`).
    :type file_config: dict
    :param log_file: Path to the log file for tracking file processing.
    :type log_file: str
    :param kwargs: Additional keyword arguments passed to the parent class.


    1. **_init_mongo_client()**:
        Initializes a MongoDB client and returns the specified collection.

        :return: A MongoDB collection object for performing database operations.
        :rtype: pymongo.collection.Collection

    2. **load_mongo_data()**:
        Reads, formats, and loads data into MongoDB. Ensures that files are not processed multiple times.

        - If the file has already been processed, it logs a warning and exits.
        - Reads data using the inherited `read_dictionary()` method.
        - Formats fields using `_format_mongo_fields()`.
        - Loads formatted data into MongoDB using `_init_mongo_client()` and `insert_many()`.

        :return: Whether the data insertion was acknowledged by MongoDB.
        :rtype: bool or None

    **Example Usage**::

        from modules.db.mongo_db import LoadMongo

        mongo_config = {
            'url': 'mongodb://localhost:27017',
            'Db': 'my_database',
            'Collection': 'my_collection'
        }
        
        file_config = {
            'file_path': '/path/to/input/file.csv'
        }

        log_file = '/path/to/log/file.log'

        loader = LoadMongo(mongo_config, file_config, log_file)

        # Load data into MongoDB
        result = loader.load_mongo_data()
        
        if result:
            print("Data successfully loaded into MongoDB!")
        else:
            print("No data was loaded.")
    """
    def __init__(self, mongo_config, file_config, log_file, **kwargs):
        self.mongo_config = mongo_config
        super().__init__(file_config, log_file, **kwargs)

    
    def _init_mongo_client(self):
        mng_client = MongoClient(self.mongo_config['url'])
        mng_db = mng_client[self.mongo_config['Db']]
        mng_collection = mng_db[self.mongo_config['Collection']]
        return mng_collection

    def load_mongo_data(self):
        """
        Loads data from an input file into a MongoDB collection.

        - Checks if the file has already been processed using `file_already_read`.
          If so, logs a warning and exits without processing further.
        """        
        if self.file_already_read:
            etl_mongo_logger.warning(f"File {self.file_name} already processed. quitting.")
            return None
        
        data_load = self.read_dictionary()

        if not data_load:
            return None
        etl_mongo_logger.warning(f"Loading Data from file {self.file_name} into MongoDB")
        client_collection = self._init_mongo_client()
        response = client_collection.insert_many([x.model_dump() for x in data_load])

        if response.acknowledged:
            self.log_file_processed
        return response.acknowledged
