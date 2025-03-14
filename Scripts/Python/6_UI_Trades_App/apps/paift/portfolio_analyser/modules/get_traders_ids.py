from modules.requests_abstraction import make_request_to_lambro
from modules.local_logger import scarp_logger

import json

def get_traders_identifiers(endpoint: str, user:str, group: str):
    """
    Get the unique trader ids from API.
    """
    try:
        traders_ids = make_request_to_lambro(endpoint_url=endpoint, user=user, groups=group)
    except Exception as exc:
        scarp_logger.error(f"For user {user} an error occured while retriving trader ids from lambro api : {exc}")
        return list()
    if traders_ids.status_code != 200:
        scarp_logger.error(f"For user {user} an unexpected http status code was recieved while retriving trader ids from lambro api : {traders_ids.status_code}")
        return list()
    response_list = json.loads(traders_ids.text)
    if not response_list:
        return list()
    return response_list

