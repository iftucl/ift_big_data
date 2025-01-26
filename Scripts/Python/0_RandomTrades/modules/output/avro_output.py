"""

UCL -- Institute of Finance & Technology
Author  : Luca Cocconcelli
Lecture : 2024-02-22
Topic   : Avro output

"""


import os
import avro.schema
from avro.datafile import DataFileWriter, DataFileReader
from avro.io import DatumReader, DatumWriter

class AvroFileOperations:
    """Class to output avro file to file system"""
    def __init__(self, output_list: list, schema: str):        
        self.schema = schema
        self.output_list = output_list

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
                reader = DataFileReader(avro_reader, DatumReader)
                input_data = [row for row in reader]
                reader.close()

        return input_data
    
    def write_table(self, file_path : str, write_ctl : bool = True):
        
        with open(file_path, 'wb') as avro_writer:
            writer = DataFileWriter(avro_writer, DatumWriter(), self._schema)
            [writer.append(row) for row in self.output_list]
            writer.close()
        
        if write_ctl:
            ctl_file_name = file_path.replace('avro', 'ctl')
            with open(ctl_file_name, 'w') as document: pass



