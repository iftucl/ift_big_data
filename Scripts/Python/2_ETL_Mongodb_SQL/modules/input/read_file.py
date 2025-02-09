"""

UCL -- Institute of Finance & Technology
Author  : Luca Cocconcelli
Lecture : 2022-11-17
Topic   : Main.py
Project : MongoDB Trades uploader
Desc    : Class to find, read and return latest file in specific directory.
          Please, note, file conventions expects datetime stamp as %Y%m%d%H%M%S
          before '.' file name extension. This is used to sort latest file.


"""


import os
import csv
from datetime import datetime

from modules.utils.info_logger import etl_postgres_logger

class ReadInputFiles:
    """
    Arguments:
        file_path (str): Path to the trade file repository
        signature: file name convention
        log_file (str): latest file read and loaded

    Public methods:
        read_csv_dictionary: returns list of ordered dictionaries.

    """


    def __init__(self, file_path, signature, log_file):
        self.file_path = file_path
        self.signature = signature
        self.log_file = log_file

    def _get_input_files_ctl(self):
        file_list = os.listdir(self.file_path)
        ctl_list = [ctl for ctl in file_list if ctl.split('.')[1] == 'ctl']

        if len(ctl_list) is 0:
            raise ValueError()

        sorted_ctl = sorted(ctl_list, key=lambda filename: datetime.strptime(filename[-18:-4], '%Y%m%d%H%M%S'), reverse=True)
        return sorted_ctl
    
    def _read_logged_file(self):
        with open('./static/file_load_logger.txt') as f:
            lines = f.readlines()
        return lines[0]

    def get_latest_input_file(self):
        ctl_files = self._get_input_files_ctl()
        latest_ctl = ctl_files[0]
        # add here check if same of last logged file
        latest_csv = latest_ctl.replace('ctl', 'csv')
        return latest_csv

    def read_csv_dictionary(self):
        file_name = self.get_latest_input_file()
        
        if file_name == self._read_logged_file():
            etl_postgres_logger.warning('logged file equal to current - data will not load to MongoDB', 'warning')
            return None

        file_path_csv = os.path.join(self.file_path, file_name)
        worksheet = []

        with open(file_path_csv) as flpt:
            reader = csv.DictReader(flpt, delimiter=',')
            for row in reader:
                worksheet.append(row)
        
        return worksheet




