"""

UCL -- Institute of Finance & Technology
Author  : Luca Cocconcelli
Lecture : 2024-02-22
Topic   : Read / Write Parquet Files

"""


import pyarrow.parquet as pq


class ParquetFileOperations:

    def __init__(self, pq_schema):        
        self.pq_schema = pq_schema
    
    def read_table(self, file_path : str):
        parq_input = pq.read_table(file_path, schema=self.pq_schema)
        self.input_data = parq_input.to_pylist()
        return self.input_data




