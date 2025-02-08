"""

UCL -- Institute of Finance & Technology
Author  : Luca Cocconcelli
Lecture : 2025-01-18
Topic   : info_logger utils

"""
from ift_global.utils.logger import IFTLogger

etl_duckdb_logger = IFTLogger(app_name="big_data", service_name="etl_duckdb", log_level="info")
