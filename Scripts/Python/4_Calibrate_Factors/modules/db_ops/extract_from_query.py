from sqlalchemy import text

from modules.db_ops.postgres_config import PostgresConfig
from modules.db_ops.ift_sql import DatabaseMethods
from modules.utils.local_logger import calibration_logger


def get_postgres_data(sql_query: str, **kwargs):
    """
    Get postgres data given a text query.

    :param: sql_query: text query like "SELECT * FROM equity_static"    
    """
    pg_config = PostgresConfig(username=kwargs.get("username"),
                               password=kwargs.get("password"),
                               host=kwargs.get("host"),
                               port=kwargs.get("port"),
                               database=kwargs.get("database"))
    print(pg_config)
    with DatabaseMethods("postgres",
                         username=pg_config.username,
                         password=pg_config.password,
                         host=pg_config.host,
                         port=pg_config.port,
                         database=pg_config.database) as db:
        try:
            result = db.session.execute(text(sql_query))
            return result.all()
        except Exception as e:
            calibration_logger.error(f"An error occurred: {e}")
            raise



