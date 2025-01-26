"""

UCL -- Institute of Finance & Technology
Author  : Luca Cocconcelli
Lecture : 2024-02-22
Topic   : Read / Write Parquet Files

"""

import pyarrow as pa
import pyarrow.parquet as pq


class ParquetFileOperations:

    def __init__(self, output_list: list, pq_schema):
        self.output_list = output_list
        self.pq_schema = pq_schema
    
    def write_table(self, file_path : str, write_ctl : bool = True):        
        # to parquet table
        try:
            output_table = pa.Table.from_pylist(self.output_list, schema=self.pq_schema)
        except AttributeError as ae:
            raise AttributeError('Incorrect data in output data list') from ae
        # write to fs
        pq.write_table(output_table, file_path, compression='BROTLI')
        if write_ctl:
            ctl_file_name = file_path.replace('parquet', 'ctl')
            with open(ctl_file_name, 'w') as document: pass
    
    def read_table(self, file_path : str):
        parq_input = pq.read_table(file_path, schema=self.pq_schema)
        return parq_input.to_pylist()




