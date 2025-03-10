import requests
from typing import Dict, Any, Literal

def make_request_to_lambro(endpoint_url: str, user: str, groups: str, method: Literal["GET", "PUT", "POST", "DELETE"] = "GET", data: Dict[str, Any] = None) -> requests.Response:
    # Build the headers
    headers = {
        "X-Forwarded-Username": user,
        "X-Forwarded-Groups": groups
    }

    # Make the request
    if method.upper() == "POST":
        if data is not None:
            # Use json parameter to automatically set Content-Type to application/json
            response = requests.post(endpoint_url, headers=headers, json=data)
        else:
            raise ValueError("Data must be provided for POST requests")
    elif method.upper() == "PUT":
        if data is not None:
            # Use json parameter to automatically set Content-Type to application/json
            response = requests.put(endpoint_url, headers=headers, json=data)
        else:
            raise ValueError("Data must be provided for PUT requests")
    elif method.upper() == "DELETE":
        if data is not None:
            # Use json parameter to automatically set Content-Type to application/json
            response = requests.delete(endpoint_url, headers=headers, json=data)
        else:
            raise ValueError("Data must be provided for PUT requests")
    elif method.upper() == "GET":
        response = requests.get(endpoint_url, headers=headers)
    else:
        raise ValueError("Unsupported method. Only GET, PUT, DELETE and POST are supported.")

    return response
