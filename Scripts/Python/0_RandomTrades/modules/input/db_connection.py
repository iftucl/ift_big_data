from sqlalchemy import create_engine, exc, engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.sql import text


class DataBaseConnect:
    """
    Class to interact with sqlite database stored within
    this git repo or docker container postgresql database.
    """
    def __init__(self, sql_config, db_type):
        self.sql_config = sql_config
        self.db_type = db_type
        self.session_local = self._db_connect()

    def _conn_postgres(self):
        """method to build postgres engine"""
        url_object = engine.URL.create(drivername = 'postgresql', 
                                       username = self.sql_config['Username'],
                                       password = self.sql_config['Password'],
                                       host = self.sql_config['Host'],
                                       database = self.sql_config['Database'],
                                       port = self.sql_config['Port'])
        try:
            connection_engine = create_engine(url_object).execution_options(autocommit=True)
            return connection_engine
        except Exception as genericErr:
            raise Exception('Error occurred while attempting to create postgresql engine') from genericErr
        
    def _db_connect(self):
        """method to generate session"""
        if self.db_type.lower() == 'postgres':
            engine = self._conn_postgres()
        elif self.db_type.lower() == 'sqlite':
            engine = create_engine(self.sql_config['FilePath'])
        else:
            raise exc.ArgumentError('Only two values are expected for db_type: postgres or sqlite')
        
        return sessionmaker(bind=engine, autocommit=False, autoflush=False)

    def get_data_query(self, sql_query):
        """method to query data from sql"""
        statement = text(sql_query)
        Session = scoped_session(self.session_local)
        s = Session()
        output =  s.execute(statement)
        return output.mappings().all()
    
    def close_conn(self):
        self.session_local.close_all
