"""

UCL -- Institute of Finance & Technology
Author  : Luca Cocconcelli
Lecture : 2025-02-02
Topic   : Main.py
Project : MongoDB Trades uploader
Desc    : Class to find, read and return latest file in specific directory.
          Please, note, file conventions expects datetime stamp as %Y%m%d%H%M%S
          before '.' file name extension. This is used to sort latest file
"""


import os
from datetime import datetime
from ift_global import MinioFileSystemRepo

from modules.utils.info_logger import etl_duckdb_logger
from modules.input.avro_input import AvroFileOperations
from modules.input.csv_input import CsvFileOperations
from modules.input.parquet_input import ParquetFileOperations
from static.RNDTRADE import generate_parquet_schema

class ReadInputFiles:
    """
    Arguments:
        file_path (str): Path to the trade file repository
        signature: file name convention
        log_file (str): latest file read and loaded

    Public methods:
        read_csv_dictionary: returns list of ordered dictionaries.
    -----
    Usage
        class_reader = ReadInputFiles(conf['params']['OutputFile'])
        class_reader.get_latest_input_file()

    """

    def __init__(self, file_config, log_file = './static/file_load_logger.txt'):
        self.file_path = file_config['DataLake']
        self.log_file = log_file
        self.file_config = file_config
        self.file_name, self.file_type = self.get_latest_input_file()
    
    def _minio_client(self):
        return  MinioFileSystemRepo(bucket_name="iftbigdata")
    @property
    def minio_client(self):
        return self._minio_client()

    def _get_input_files_ctl(self):
        file_list = self.minio_client.list_files(self.file_path)
        ctl_list = [ctl for ctl in file_list if ctl.split('.')[1] == 'ctl']

        if not ctl_list:
            etl_duckdb_logger.warning("No ctl file can be located, returning None")
            return None

        sorted_ctl = sorted(ctl_list, key=lambda filename: datetime.strptime(filename[-18:-4], '%Y%m%d%H%M%S'), reverse=True)
        return sorted_ctl

    def _write_log_file(self, file_name):        
        with open('./static/file_load_logger.txt', 'w') as f:
            f.write(file_name)

    def _read_logged_file(self):
        """reads logged files, if not exists returns mock-up"""
        if not os.path.exists(self.log_file):
            # creates mockup if not exists
            return 'BondTrades_XXXXXXXXXXX.XYZ'
        
        with open(self.log_file) as f:
            lines = f.readlines()
        return lines[0]

    def get_latest_input_file(self):
        '''finds latest file with data and file type extension'''
        ctl_files = self._get_input_files_ctl()
        
        if not ctl_files:
            return None
                
        latest_ctl = ctl_files[0]
        for f_type in ["csv", "avro", "parquet"]:
            f_exists = self.minio_client.file_exists(latest_ctl.replace('ctl', f_type))
            if f_exists:
                return latest_ctl.replace('ctl', f_type), f_type
        return None, None
    
    @staticmethod
    def _select_read_class(file_type):
        '''Abstraction method to select the write output class'''
        class_select = {
            'parquet' : ParquetFileOperations,
            'avro' : AvroFileOperations,
            'csv' : CsvFileOperations
        }
        return class_select[file_type]

    def _set_file_schema(self, file_type):
        if file_type == 'avro':            
            return self.file_config['AvroSchema']
        elif file_type == 'csv':
            return self.file_config['ColumnNames']
        elif file_type == 'parquet':
            return generate_parquet_schema()
        else:
            raise TypeError('Not implemented write output format ')

    def read_dictionary(self) -> list[dict]:        
        class_reader = self._select_read_class(self.file_type)
        file_schema = self._set_file_schema(self.file_type)
        if not self.file_path:
            return None
        if not self.file_type == "avro":
            avr_schema = None
        else:
            avr_schema = AvroFileOperations(self.file_config['AvroSchema'])
        #read_file = class_reader(file_schema)        
        #return read_file.read_table(full_path
        file_read = self.minio_client.read_file(path=self.file_name, file_type=self.file_type, avro_schema=avr_schema)
        return file_read
    
    def __repr__(self) -> str:
        return f'Data reader : instance of class for file {self.file_name}'

