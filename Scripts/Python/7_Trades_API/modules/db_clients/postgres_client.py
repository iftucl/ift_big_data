from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any
from sqlalchemy import create_engine, engine, exc, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm.session import Session
import os



from modules.utils.local_logger import lambro_logger


class PostgresConfig(BaseModel):
    username: str | None =  Field(description="Postgres username, if Not provided will use the environment variable: POSTGRES_USERNAME")
    password: str | None =  Field(description="Postgres password, if Not provided will use the environment variable: POSTGRES_PASSWORD")
    host: str | None =  Field(description="Postgres host, if Not provided will use the environment variable: POSTGRES_HOST")
    port: str | None =  Field(description="Postgres port, if Not provided will use the environment variable: POSTGRES_PORT")
    database: str | None =  Field(description="Postgres Database Name, if Not provided will use the environment variable: POSTGRES_DATABASE")
    # validates username
    @field_validator("username", mode="after")
    @classmethod
    def get_username(cls, v) -> str:
        try:
            if not v:
                return os.environ["POSTGRES_USERNAME"]
        except KeyError:
            return None
    @field_validator("password", mode="after")
    @classmethod
    def get_password(cls, v) -> str:
        try:
            if not v:
                return os.environ["POSTGRES_PASSWORD"]
            return v
        except KeyError:
            return None
    @field_validator("host", mode="after")
    @classmethod
    def get_host(cls, v) -> str:
        try:
            if not v:
                return os.environ["POSTGRES_HOST"]
            return v
        except KeyError:
            return None
    @field_validator("port", mode="after")
    @classmethod
    def get_port(cls, v) -> str:
        try:
            if not v:
                return os.environ["POSTGRES_PORT"]
            return v
        except KeyError:
            return None
    @field_validator("database", mode="after")
    @classmethod
    def get_db(cls, v) -> str:
        if not v:
            try:           
                return os.environ["POSTGRES_DATABASE"]
            except KeyError:
                return None            
        return v


class DatabaseMethods:
    """
    A class for managing database connections and operations.

    This class provides methods to connect to SQLite or PostgreSQL databases,
    manage sessions, and perform basic database operations.

    :param db_type: The type of database ('postgres' or 'sqlite')
    :type db_type: str
    :param kwargs: Additional keyword arguments for database configuration
    :type kwargs: dict

    :ivar db_type: The type of database
    :vartype db_type: str
    :ivar username: Database username (for PostgreSQL)
    :vartype username: Optional[str]
    :ivar password: Database password (for PostgreSQL)
    :vartype password: Optional[str]
    :ivar host: Database host (for PostgreSQL)
    :vartype host: Optional[str]
    :ivar database: Database name (for PostgreSQL)
    :vartype database: Optional[str]
    :ivar port: Database port (for PostgreSQL)
    :vartype port: Optional[int]
    :ivar sql_config: Configuration for SQLite database
    :vartype sql_config: dict

    :raises exc.ArgumentError: If an invalid db_type is provided
    """

    def __init__(self, db_type: str, **kwargs):
        """
        Initialize the DatabaseMethods instance.

        :param db_type: The type of database ('postgres' or 'sqlite')
        :type db_type: str
        :param kwargs: Additional keyword arguments for database configuration
        :type kwargs: dict
        """
        self.db_type = db_type.lower()
        self.username = kwargs.get('username')
        self.password = kwargs.get('password')
        self.host = kwargs.get('host')
        self.database = kwargs.get('database')
        self.port = kwargs.get('port')
        self.sql_config = kwargs.get('SQLConfig', {})
        self._engine = self.open_client_connection(self.db_type)
        self._session_factory = sessionmaker(bind=self._engine, autocommit=False, autoflush=False)

    def __enter__(self):
        """
        Enter the runtime context related to this object.

        :return: The DatabaseMethods instance
        :rtype: DatabaseMethods
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the runtime context related to this object.

        :param exc_type: The exception type, if an exception was raised
        :param exc_val: The exception value, if an exception was raised
        :param exc_tb: The traceback, if an exception was raised
        """
        self.close()

    @property
    def connection(self) -> Engine:
        """
        Returns the database engine.

        :return: The SQLAlchemy engine object
        :rtype: Engine
        """
        return self._engine

    @property
    def session(self) -> Session:
        """
        Returns a new database session.

        :return: A new SQLAlchemy session
        :rtype: Session
        """
        return scoped_session(self._session_factory)()

    def commit(self):
        """Commits the current transaction."""
        self.session.commit()

    def close(self, commit: bool = True):
        """
        Closes the database connection.

        :param commit: Whether to commit before closing, defaults to True
        :type commit: bool
        """
        if commit:
            self.commit()
        self.session.close()
        self._engine.dispose()

    def _conn_sqlite(self) -> Engine:
        """
        Creates and returns a SQLite database engine.

        :return: SQLAlchemy engine for SQLite
        :rtype: Engine
        :raises Exception: If there's an error creating the SQLite engine
        """
        try:
            return create_engine(self.sql_config['SQLDBPath'])
        except Exception as e:
            raise Exception('Error occurred while attempting to create SQLite database engine') from e

    def _conn_postgres(self) -> Engine:
        """
        Creates and returns a PostgreSQL database engine.

        :return: SQLAlchemy engine for PostgreSQL
        :rtype: Engine
        :raises Exception: If there's an error creating the PostgreSQL engine
        """
        url_object = engine.URL.create(
            drivername='postgresql',
            username=self.username,
            password=self.password,
            host=self.host,
            database=self.database,
            port=self.port
        )
        try:
            return create_engine(url_object, pool_size=20, max_overflow=0)
        except Exception as e:
            raise Exception('Error occurred while attempting to create PostgreSQL engine') from e

    def open_client_connection(self, db_type: str) -> Engine:
        """
        Opens a new database connection based on the specified database type.

        :param db_type: The type of database ('postgres' or 'sqlite')
        :type db_type: str
        :return: SQLAlchemy engine object
        :rtype: Engine
        :raises exc.ArgumentError: If an invalid db_type is provided
        """
        if db_type == 'postgres':
            return self._conn_postgres()
        elif db_type == 'sqlite':
            return self._conn_sqlite()
        else:
            raise exc.ArgumentError('Only two values are expected for db_type: postgres or sqlite')


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
            lambro_logger.error(f"An error occurred: {e}")
            raise



