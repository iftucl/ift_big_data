import csv

class CsvFileOperations:
    '''
    CSV File Operations
    ==========

    Class to read and write csv files
    '''

    def __init__(self, output_list: list, csv_schema: str) -> None:
        self.output_list = output_list
        self.csv_schema = csv_schema
    
    def _enforce_schema(self):
        for row in self.output_list:
            if list(row.keys()) == self.csv_schema:
                return True
            else:
                raise ValueError('Csv Writer :: Unexpected column names in generated trade simulations')
            
    def write_table(self, file_path : str, write_ctl : bool = True):
        schema_check = self._enforce_schema()
        if schema_check:
            with open(file_path, "w", newline='') as csv_file:
                writer = csv.DictWriter(csv_file, list(self.output_list[0].keys()), delimiter=",")
                writer.writeheader()
                for row in self.output_list:                
                    writer.writerow(row)
                    
            if write_ctl:
                with open(file_path.replace('csv', 'ctl'), 'w') as document: pass       

    def read_table(self, file_path):

        input_data = []
        with open(file_path) as flpt:
            reader = csv.DictReader(flpt, delimiter=',')
            for row in reader:
                input_data.append(row)
        
        return input_data
    

