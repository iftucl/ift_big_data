"""

UCL -- Institute of Finance & Technology
Author  : Luca Cocconcelli
Lecture : 2022-11-18
Topic   : info_logger utils

"""

from ift_global.utils.logger import IFTLogger

etl_postgres_logger = IFTLogger(app_name="big_data", service_name="etl_mongo_postgres", log_level="info")
