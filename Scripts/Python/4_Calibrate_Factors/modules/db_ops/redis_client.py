import redis
import json
import os

from modules.utils.local_logger import calibration_logger
# Connect to Redis
def get_redis_client(**kwargs):
    """
    Set-up redis client connection.

    """
    try:
        redis_client = redis.Redis(host=kwargs.get("redis_host") or os.environ["REDIS_HOST"],
                                   port=kwargs.get("redis_port") or os.environ["REDIS_PORT"],
                                   db=0)
        _ = redis_client.ping()
        return redis_client
    except Exception as exc:
        calibration_logger.error(f"An error occurred while trying to establish redis connection.")
        return None


# Function to store company parameters
def store_company_params(company_id, params, **kwargs):
    """
    Load the market param to redis.    
    """
    # get redis client
    redis_client = get_redis_client(**kwargs)
    #- create redis key for company
    key = f"company:{company_id}"
    # we store params as json
    json_data = json.dumps(params, default=str)
    
    if redis_client is None:
        raise ValueError(f"Failed to establish redis client connection. Quitting.")
    
    #redis_client.json().set(key, '$', json_data)
    redis_client.set( key, json_data)

# Function to retrieve company parameters
def get_company_params(company_id, **kwargs):
    """
    Retrieve market param from redis.
    """
    redis_client = get_redis_client(**kwargs)
    if redis_client is None:
        return None
    key = f"company:{company_id}"
    json_data = redis_client.get(key)
    
    return json.loads(json_data) if json_data else None
