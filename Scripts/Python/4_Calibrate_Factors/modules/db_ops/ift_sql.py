from typing import Optional, Any, Dict
from contextlib import contextmanager

from sqlalchemy import create_engine, exc
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.orm.session import Session


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
    :ivar _engine: Underlying SQLAlchemy Engine
    :vartype _engine: Engine
    :ivar _session_factory: SQLAlchemy session factory
    :vartype _session_factory: sessionmaker
    :ivar _scoped_session: Scoped session registry
    :vartype _scoped_session: scoped_session

    :raises exc.ArgumentError: If an invalid db_type is provided
    """

    def __init__(self, db_type: str, **kwargs: Any):
        """
        Initialize the DatabaseMethods instance.

        :param db_type: The type of database ('postgres' or 'sqlite')
        :type db_type: str
        :param kwargs: Additional keyword arguments for database configuration
        :type kwargs: dict
        """
        self.db_type = db_type.lower()
        self.username: Optional[str] = kwargs.get("username")
        self.password: Optional[str] = kwargs.get("password")
        self.host: Optional[str] = kwargs.get("host")
        self.database: Optional[str] = kwargs.get("database")
        self.port: Optional[int] = kwargs.get("port", 5432)
        self.sql_config: Dict[str, Any] = kwargs.get("SQLConfig", {})

        self._engine: Engine = self._open_client_connection()
        self._session_factory = sessionmaker(
            bind=self._engine,
            autocommit=False,
            autoflush=False,
        )
        # keep a single scoped_session, do not recreate it on every access
        self._scoped_session = scoped_session(self._session_factory)

    # ------------------------------------------------------------------ #
    # Context-manager for engine lifetime
    # ------------------------------------------------------------------ #

    def __enter__(self) -> "DatabaseMethods":
        """
        Enter the runtime context related to this object.

        :return: The DatabaseMethods instance
        :rtype: DatabaseMethods
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the runtime context related to this object.

        This will dispose the underlying engine and close all pooled
        connections, regardless of whether an exception was raised.

        :param exc_type: The exception type, if an exception was raised
        :param exc_val: The exception value, if an exception was raised
        :param exc_tb: The traceback, if an exception was raised
        """
        self.dispose()

    # ------------------------------------------------------------------ #
    # Engine and session accessors
    # ------------------------------------------------------------------ #

    @property
    def connection(self) -> Engine:
        """
        Returns the database engine.

        :return: The SQLAlchemy engine object
        :rtype: Engine
        """
        return self._engine

    @property
    def engine(self) -> Engine:
        """
        Alias for :pyattr:`connection`.

        :return: The SQLAlchemy engine object
        :rtype: Engine
        """
        return self._engine

    @property
    def session(self) -> Session:
        """
        Returns the current scoped session.

        Note: This returns a `Session` associated with the scoped_session
        registry. Do not close or dispose the engine here; prefer using
        :meth:`session_scope` for transactional work.

        :return: A SQLAlchemy session
        :rtype: Session
        """
        return self._scoped_session

    # ------------------------------------------------------------------ #
    # Transaction / lifecycle helpers
    # ------------------------------------------------------------------ #

    @contextmanager
    def session_scope(self):
        """
        Provide a transactional scope around a series of operations.

        Within this context:

        * The session is committed if no exceptions are raised.
        * The session is rolled back if an exception occurs.
        * The session is removed from the scoped registry on exit.

        Example::

            with db.session_scope() as session:
                session.add(obj)
                session.query(...)

        :return: A context-managed SQLAlchemy session
        :rtype: Session
        """
        session = self.session
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            # remove the current session from the scoped registry
            self._scoped_session.remove()

    def commit(self):
        """Commits the current transaction on the scoped session."""
        self.session.commit()

    def dispose(self) -> None:
        """
        Dispose the database engine and remove the scoped session.

        This closes all connections in the pool and should be called when
        you are completely done using this DatabaseMethods instance.
        """
        # remove scoped session bindings first
        self._scoped_session.remove()
        self._engine.dispose()

    # ------------------------------------------------------------------ #
    # Internal connection creation
    # ------------------------------------------------------------------ #

    def _conn_sqlite(self) -> Engine:
        """
        Creates and returns a SQLite database engine.

        Expects ``SQLConfig['SQLDBPath']`` to contain a valid SQLAlchemy
        SQLite URL (e.g. ``'sqlite:///mydb.sqlite3'``).

        :return: SQLAlchemy engine for SQLite
        :rtype: Engine
        :raises ValueError: If the SQLite path is missing
        :raises Exception: If there's an error creating the SQLite engine
        """
        db_path = self.sql_config.get("SQLDBPath")
        if not db_path:
            raise ValueError("SQLite configuration missing 'SQLDBPath'")
        try:
            return create_engine(db_path)
        except Exception as e:
            raise Exception(
                "Error occurred while attempting to create SQLite database engine"
            ) from e

    def _conn_postgres(self) -> Engine:
        """
        Creates and returns a PostgreSQL database engine.

        The following attributes should be set on the instance:
        ``username``, ``password``, ``host``, ``database``, and optionally ``port``.

        :return: SQLAlchemy engine for PostgreSQL
        :rtype: Engine
        :raises Exception: If there's an error creating the PostgreSQL engine
        """
        url_object = URL.create(
            drivername="postgresql",
            username=self.username,
            password=self.password,
            host=self.host,
            database=self.database,
            port=self.port,
        )
        try:
            return create_engine(url_object, pool_size=20, max_overflow=0)
        except Exception as e:
            raise Exception(
                "Error occurred while attempting to create PostgreSQL engine"
            ) from e

    def _open_client_connection(self) -> Engine:
        """
        Opens a new database connection based on the specified database type.

        :return: SQLAlchemy engine object
        :rtype: Engine
        :raises exc.ArgumentError: If an invalid db_type is provided
        """
        if self.db_type == "postgres":
            return self._conn_postgres()
        elif self.db_type == "sqlite":
            return self._conn_sqlite()
        else:
            raise exc.ArgumentError(
                "Only two values are expected for db_type: postgres or sqlite"
            )
