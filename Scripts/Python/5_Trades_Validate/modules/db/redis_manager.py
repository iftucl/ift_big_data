import redis
import os
from typing import Optional
from modules.utils import trades_validate_logger
import json

def check_redis_config(host_name: str | None = None, redis_port: int | None = None):
    if not host_name:
        try:
            host_name = os.environ["REDIS_HOST"]
        except KeyError:
            trades_validate_logger.error("Could not find redis host env variable. please make sure REDIS_HOST name is correctly exported")
            raise
    if not redis_port:
        try:
            redis_port = os.environ["REDIS_PORT"]
        except KeyError:
            trades_validate_logger.error("Could not find redis port env variable. please make sure REDIS_PORT name is correctly exported")
            raise
    return host_name, redis_port


# Initialize Redis connection
def get_redis_connection(host_name: Optional[str] = None, redis_port: Optional[int] = None) -> redis.StrictRedis:
    host_redis, port_redis = check_redis_config(host_name=host_name, redis_port=redis_port)
    return redis.StrictRedis(
        host=host_redis,
        port=port_redis,
        db=0,
        decode_responses=True  # Ensures strings are returned instead of bytes
    )

# Check if a file has already been processed
def is_file_processed(file_name: str, host_name: Optional[str] = None, redis_port: Optional[int] = None) -> int:
    """
    Checks if the given file name exists in the Redis set of processed files.

    :param redis_conn: Redis connection object
    :param file_name: Name of the file to check
    :return: True if the file has been processed, False otherwise
        >>> file_name = "example_file.csv"
        >>> is_file_processed(file_name, redis_host='localhost', redis_port=6379)
    """
    redis_conn = get_redis_connection(host_name=host_name, redis_port=redis_port)
    return redis_conn.sismember('processed_files_mongoetl', file_name)

# Add a file to the set of processed files
def mark_file_as_processed(file_name: str, host_name: Optional[str] = None, redis_port: Optional[int] = None):
    """
    Marks a file as processed by adding it to the Redis set.

    :param redis_conn: Redis connection object
    :param file_name: Name of the file to mark as processed

    :Example:
        >>> file_name = "example_file.csv"
        >>> mark_file_as_processed(file_name, redis_host='localhost', redis_port=6379)
    """
    redis_conn = get_redis_connection(host_name=host_name, redis_port=redis_port)
    redis_conn.sadd('processed_files', file_name)

# Function to retrieve company parameters
def get_company_params(company_id, **kwargs):
    """
    Retrieve market param from redis.
    """
    redis_client = get_redis_connection(**kwargs)
    if redis_client is None:
        return None
    key = f"company:{company_id}"
    json_data = redis_client.get(key)
    
    return json.loads(json_data) if json_data else None
