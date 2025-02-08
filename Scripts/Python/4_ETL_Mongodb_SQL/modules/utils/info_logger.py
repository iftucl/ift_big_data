"""

UCL -- Institute of Finance & Technology
Author  : Luca Cocconcelli
Lecture : 2022-11-18
Topic   : info_logger utils

"""

import datetime

#-- Print info log
#--- helper/util function for logging script info into console
# args:
#   type = 'progress'
#   msg = 'test message'

def print_info_log(msg, type):
    now_time = datetime.datetime.now()
    msg_out = now_time.strftime('%Y-%m-%d %H:%M:%S') + ' --- [ ' + type.upper() + ' ] --- ' + msg
    print(msg_out)

