"""

UCL -- Institute of Finance & Technology
Author  : Luca Cocconcelli
Lecture : 2024-02-22
Topic   : Write Output File

"""

from datetime import datetime

from modules.output.avro_output import AvroFileOperations
from modules.output.csv_output import CsvFileOperations
from modules.output.parquet_output import ParquetFileOperations
from static.RNDTRADE import generate_parquet_schema

from ift_global import MinioFileSystemRepo


class WriteOutputFile:
    """
    WriteOutputFile
    =========

    Abstraction layer to call different types of output writer
    ---

    Notes:
        accept file_type only avro, csv and parquet
    
    """
    def __init__(self, file_config, file_type):
        self.file_type = file_type
        self.file_path, self.file_name = file_config['FilePath'], file_config['FileName']
        self.file_schema = self._set_file_schema(file_config)
        self.full_path = self._get_full_path()
        self.object_writer = self._class_selector()

    def _minio_client(self):
        minio_client_init = MinioFileSystemRepo(bucket_name='iftbigdata')
        return minio_client_init
    
    @property
    def minio_client(self):
        return self._minio_client()

    def _set_file_schema(self, file_config):
        if self.file_type == 'avro':            
            return file_config['AvroSchema']
        elif self.file_type == 'csv':
            return file_config['ColumnNames']
        elif self.file_type == 'parquet':
            return generate_parquet_schema()
        else:
            raise TypeError('Not implemented write output format ')


    def _get_full_path(self):
        '''method to construct full file path'''
        full_path =  '{}/{}{}.{}'.format(self.file_path,  
                                         self.file_name, 
                                         datetime.strftime(datetime.now(), "%Y%m%d%H%M%S"),
                                         self.file_type)
        return full_path

    def _class_selector(self):
        '''Abstraction method to select the write output class'''
        class_select = {
            'parquet' : ParquetFileOperations,
            'avro' : AvroFileOperations,
            'csv' : CsvFileOperations
        }

        return class_select[self.file_type]    
    def write_output(self, output_data: list):
        try:            
            wb_write = self.object_writer([x.model_dump() for x in output_data], self.file_schema)
            wb_write.write_table(self.full_path)
        except IOError:
            print(f'Error writing to {self.file_type} file')
    def write_output_minio(self, output_data: list, file_type: str = "csv"):
        try:
            self.minio_client.write_file(path=self.full_path, output_data=[x.model_dump() for x in output_data], file_type=file_type)            
        except IOError as iexc:
            print(f'Error writing to {self.file_type} file to Minio')
            print(iexc)
            