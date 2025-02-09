"""

UCL -- Institute of Finance & Technology
Author  : Luca Cocconcelli
Lecture : 2022-11-19
Topic   : sqlite_db.py
Project : ETLSQLite
Desc    : sqlite client to load data to sqlite db


"""
import sqlite3
from modules.db.mongo_db import GetMongo

class SQLiteLoader(GetMongo):
    def __init__(self, mongo_config, business_date, sql_config):
        super().__init__(mongo_config, business_date)
        self.sql_config = sql_config
        self._conn = sqlite3.connect(sql_config['SQLDBPath'])
        self._cursor = self._conn.cursor()
        self.data_load = self.aggregate_to_load()

    def __enter__(self):
        return self

    def __exit__(self):
        self.close()

    @property
    def connection(self):
        return self._conn

    @property
    def cursor(self):
        return self._cursor

    def commit(self):
        self.connection.commit()

    def close(self, commit=True):
        if commit:
            self.commit()
        self.connection.close()

    def execute(self, sql, params=None):
        self.cursor.execute(sql, params or ())



    def _check_sql_table(self):
        
        query = """CREATE TABLE IF NOT EXISTS {table_name} (
                 pos_id TEXT PRIMARY KEY, 
                 cob_date TEXT NOT NULL,
                 trader TEXT NOT NULL,
                 isin TEXT NOT NULL,
                 ccy TEXT NOT NULL,
	             net_quantity INTEGER NOT NULL,
	             net_amount INTEGER NOT NULL)""".format(table_name=self.sql_config['Table'])
        
        query_output = self.execute(query)
        
        return query_output
    
    def upsert_position_set(self):

        self._check_sql_table()

        for docs in self.data_load:

            query = """INSERT INTO {sql_table}(pos_id,cob_date,trader,isin,ccy,net_quantity,net_amount) 
                   VALUES("{pos_id}","{cob_date}","{trader}","{isin}","{ccy}",{net_quantity},{net_amount})
                   ON CONFLICT(pos_id) DO UPDATE SET 
                   net_amount={net_amount}, 
                   net_quantity={net_quantity};""".format(
                    sql_table=self.sql_config['Table'],
                    pos_id=docs['pos_id'],
                    cob_date=docs['cob_date'],
                    trader=docs['trader'],
                    isin=docs['isin'],
                    ccy=docs['ccy'],
                    net_quantity=docs['net_quantity'],
                    net_amount=docs['net_amount']
                   )
            print(query)
            self.execute(query)
        
