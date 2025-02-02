"""

UCL -- Institute of Finance & Technology
Author  : Luca Cocconcelli
Lecture : 2024-02-22
Topic   : Avro output

"""


import os
import avro.schema
from avro.datafile import DataFileReader
from avro.io import DatumReader

class AvroFileOperations:
    """Class to output avro file to file system"""
    def __init__(self, schema: str):        
        self.schema = schema
        self.input_data = []

    @property
    def schema(self):
        return self._schema
    
    @schema.setter
    def schema(self, file_path):        
        if not os.path.exists(file_path):
            raise FileExistsError('Avro schema file does not exist')
        else:
            with open(file_path, 'rb') as avr_scm:
                avro_schema = avro.schema.parse(avr_scm.read())
                self._schema = avro_schema
    
    def read_table(self, file_path):
        if not os.path.exists(file_path):
            raise FileNotFoundError('Avro file not found')
        else:
            with open(file_path, 'rb') as avro_reader:
                reader = DataFileReader(avro_reader, DatumReader())
                self.input_data = [row for row in reader]
                reader.close()

        return self.input_data



