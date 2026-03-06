import os
import time
from typing import Literal, Optional

import duckdb
import duckdb_extension_httpfs
import duckdb_extensions
import pandas as pd
from duckdb_extensions.extension_importer import import_extension
from ift_global.utils.string_utils import trim_string

"""
.. warning:
    duckdb-extensions & duckdb-extension-httpfs extra python libraries are installed as a workaround
    to get httpfs extension for duckdb. This problem arose when we had network failures in retrieving and
    installing httpfs from duckdb website. Hopefully in the future, this problem will be fixed by duckdb with
    extension management implemented and supported by official duck db distribution. (https://github.com/duckdb/duckdb/discussions/8030)
"""

if not duckdb.sql("SELECT installed FROM duckdb_extensions() where extension_name='httpfs'").fetchone()[0]:
    try:
        import_extension("httpfs", force_install=True)
    except Exception as exc:
        print(f"Httpfs installation failed as exception was: {exc}")
 
class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        instance = cls._instances.get(cls)
        if instance is None or not instance._is_connection_valid():
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return instance

    def reset_instance(cls):
        if cls in cls._instances:
            del cls._instances[cls]

# (metaclass=SingletonMeta):
class DuckDBMinioReader:
    def __init__(self, bucket_name, minio_uri: str | None=None, **kwargs):
        """
        Duckdb client to read from MinIO.        
        """
        self.minio_uri=minio_uri
        self.user=kwargs.get("user") or os.environ["MINIO_USER"]
        self.password=kwargs.get("password") or os.environ["MINIO_PASSWORD"]
        self.endpoint_url=kwargs.get("endpoint_url") or os.environ["MINIO_URL"]
        self.use_ssl = kwargs.get("use_ssl", True)
        self.bucket_name = bucket_name or os.environ["MINIO_BUCKET"]
        self.minio_region = kwargs.get("region") or os.environ["MINIO_REGION"]
        self.con = self._connect()
        self._setup_httpfs()

    def _connect(self):
        if self.minio_uri:
            self._setup_httpfs()
            return duckdb.connect(self.minio_uri)
        return duckdb.connect()

    def _validate_minio_url(self):
        minio_domain = self.endpoint_url.replace("https://", "")
        return trim_string(minio_domain, "trailing", "/")

    @property
    def minio_endpoint(self):
        return self._validate_minio_url()

    def _is_connection_valid(self) -> bool:
        try:
            self.con.execute("SELECT 1")
            return True
        except Exception:
            return False
    
    # set config
    def _setup_httpfs(self):
        if not self.con.sql("SELECT installed FROM duckdb_extensions() where extension_name='httpfs'").fetchone()[0]:
            try:
                duckdb.execute("INSTALL httpfs;")
            except Exception as exc:
                print(f"Httpfs installation failed as exception was: {exc}")
        self.con.execute("LOAD httpfs;")
        self.con.execute(f"SET s3_endpoint='{self.minio_endpoint}';")
        self.con.execute(f"SET s3_access_key_id='{self.user}';")
        self.con.execute(f"SET s3_region='{self.minio_region}'")
        self.con.execute(f"SET s3_secret_access_key='{self.password}';")
        self.con.execute("SET s3_url_style='path';")
        self.con.execute(f"SET s3_use_ssl={self.use_ssl};")
    
    # read csv
    def read_csv(self, path, custom_query: Optional[str]=None, retries=5, delay=5):
        """
        path: str, local path or s3://bucket/key for MinIO
        custom_query: if the user passes a custom query it will executed.
                     the custom query must contain '{path}' to successfully be executed.
                     Defaults to none. If none the entire file will be read.
        Returns: pandas.DataFrame
        """
        if custom_query and "{path}" not in custom_query:
            raise ValueError("The query must include a '{path}' placeholder.")
        
        if custom_query:
            execute_query=custom_query.format(path=f"read_csv_auto('{path}')")
        else:
            execute_query=f"SELECT * FROM read_csv_auto('{path}')"

        for attempt in range(retries):
            try:
                return self.con.execute(execute_query).df()
            except Exception as e:
                print(f"Attempt {attempt+1} failed: {e}")
                time.sleep(delay)
        raise RuntimeError(f"All retries to write csv failed with Exception")
        
    def write_csv(self, what: pd.DataFrame, path: str, retries=5, delay=5):
        """
        Writes a csv to Minio
        """
        norm_path = normalise_minio_path(path=path)
        what_df = what
        for attempt in range(retries):
            try:
                return self.con.execute(f"COPY what_df TO '{norm_path}' WITH DELIMITER ',' CSV HEADER")
            except Exception as e:
                print(f"Attempt {attempt+1} failed: {e}")
                time.sleep(delay)
        raise RuntimeError(f"All retries to write csv failed with Exception")
    # read parquet
    def read_parquet(self, path, custom_query: Optional[str]=None):
        """
        Read parquet file from MinIO.
        
        path: str, local path or s3://bucket/key for MinIO
        custom_query: if the user passes a custom query it will executed.
                     the custom query must contain '{path}' to successfully be executed.
                     Defaults to none. If none the entire file will be read.
        Returns: pandas.DataFrame
        """
        if custom_query and "{path}" not in custom_query:
            raise ValueError("The query must include a '{path}' placeholder.")
        
        if custom_query:
            exectue_query=custom_query.format(path=f"read_parquet('{path}')")
        else:
            exectue_query=f"SELECT * FROM read_parquet('{path}')"
        return self.con.execute(exectue_query).df()
    
    def write_parquet(self, what: pd.DataFrame, path: str, compression_type: Literal["SNAPPY", "ZSTD"]="SNAPPY"):
        """
        Write a parquet to Minio.
        
        :param what: a pandas dataframe.
        :type what: pd.DataFrame
        :param compression_type: compression type for parquet files.
        :type compression_type: Literal["SNAPPY", "ZSTD"]
        """
        norm_path = normalise_minio_path(path=path)
        what_df = what
        self.con.execute(f"COPY what_df TO '{norm_path}' WITH (FORMAT PARQUET, COMPRESSION {compression_type})")
    
    def write_ctl(self, what: pd.DataFrame, path: str):
        """
        Write a control file to Minio to mark a input bundle completed.
        """
        norm_path = normalise_minio_path(path=path)
        what_df = what
        self.con.execute(f"COPY what_df TO '{norm_path}' WITH DELIMITER ',' CSV HEADER")


def normalise_minio_path(path: str) -> str:
    """
    Normalise path to minio with s3 conventions.

    :param path: a string represing a minio file.
    :type path: str
    :return: _description_
    :rtype: str
    """
    if path.startswith("s3://"):
        return path
    
    if path.startswith("/"):
        return "s3:/" + path
    
    return "s3://" + path
