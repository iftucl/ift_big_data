from sqlalchemy import exc, create_engine, engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.sql import text
from sqlalchemy.dialects.postgresql import insert

from modules.data_models.port_position_model import PortfolioPositions

class DatabaseMethods:
    """
    Database Methods
    ==================

    Notes
    ------------------
    setup database client for SQLite or Postgres
    
    Methods
    ------------------
    
    """

    def __init__(self, sql_config, db_type):
        self.sql_config = sql_config
        self._conn = self.open_client_connection(db_type)

    def __enter__(self):
        return self

    def __exit__(self):
        self.close()

    @property
    def connection(self):
        return self._conn
    
    def commit(self):
        self.connection.commit()

    def close(self, commit=True):
        if commit:
            self.commit()
        self.connection.close()

    def execute(self, ops_type, sql_statement=None, data_load=None):
        Session = scoped_session(self._conn)
        s = Session()
        if ops_type == 'upsert':
            stmt = insert(PortfolioPositions).values(data_load)
            stmt = stmt.on_conflict_do_update(
                index_elements=['pos_id'],
                set_= dict({
                    'net_amount': stmt.excluded.net_amount,
                    'net_quantity': stmt.excluded.net_quantity
                    })
                )
            output =  s.execute(stmt)
            s.commit()
            return output.is_insert
        elif ops_type == 'read':
            output =  s.execute(text(sql_statement))
            return output.mappings().all()
        else:
            raise TypeError('Database method not supported. Only read and write.')

    def _conn_sqlite(self):
        try:
            connection_engine = create_engine(self.sql_config['SQLDBPath'])
            return connection_engine
        except Exception as genericErr:
            raise Exception('Error occured while attempting to create sqlite db engine') from genericErr
    
    def _conn_postgres(self):
        url_object = engine.URL.create(drivername = 'postgresql', 
                                       username = self.sql_config['Username'],
                                       password = self.sql_config['Password'],
                                       host = self.sql_config['Host'],
                                       database = self.sql_config['Database'],
                                       port = self.sql_config['Port'])
        try:
            connection_engine = create_engine(url_object, pool_size=20, max_overflow=0).execution_options(autocommit=True)
            return connection_engine
        except Exception as genericErr:
            raise Exception('Error occurred while attempting to create postgresql engine') from genericErr
    
    def open_client_connection(self, db_type):
        if db_type.lower() == 'postgres':
            engine = self._conn_postgres()
            return sessionmaker(bind=engine, autocommit=False, autoflush=False)
        elif db_type.lower() == 'sqlite':
            engine = self._conn_sqlite()
            return sessionmaker(bind=engine, autocommit=False, autoflush=False)
        else:
            raise exc.ArgumentError('Only two values are expected for db_type: postgres or sqlite')
