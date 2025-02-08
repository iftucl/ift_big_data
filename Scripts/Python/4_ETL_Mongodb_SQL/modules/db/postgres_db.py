from sqlalchemy import exc, inspect, create_engine
import sqlalchemy.orm as orm
from contextlib import contextmanager


class PostgresMethods:

    def __init__(self, **kwargs):
        if 'drivername' not in kwargs.keys():
            raise ArgumentError('drivername must be specified')        
        self.driver = kwargs['drivername']
    
    @contextmanager
    def session_context(self, engine):
        raise NotImplementedError
