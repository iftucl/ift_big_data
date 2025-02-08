import csv

class CsvFileOperations:
    '''
    CSV File Operations
    ==========

    Class to read and write csv files
    '''

    def __init__(self, csv_schema: str) -> None:
        self.input_data = []
        self.csv_schema = csv_schema
    
    def _enforce_schema(self):
        for row in self.output_list:
            if list(row.keys()) == self.csv_schema:
                return True
            else:
                raise ValueError('Csv Writer :: Unexpected column names in generated trade simulations')            

    def read_table(self, file_path):        
        with open(file_path) as flpt:
            reader = csv.DictReader(flpt, delimiter=',')
            for row in reader:
                self.input_data.append(row)
        
        return self.input_data
    

