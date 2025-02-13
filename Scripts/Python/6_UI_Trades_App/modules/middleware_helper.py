from ift_global import ReadConfig
import os
from fastapi import status
from fastapi.responses import JSONResponse
from starlette.authentication import AuthenticationBackend, AuthCredentials, SimpleUser, UnauthenticatedUser
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.exceptions import HTTPException
from ift_global.utils.string_utils import trim_string

from modules.exception_abstraction import forbidden_page, not_found

from modules.local_logger import scarp_logger

try:
    scarp_env = os.environ["SCARPASOUN_ENV"]
except KeyError:
    scarp_logger.warning(f"On start-up, 'scarp_ENV' env variable is not set. Defaulting to local env")    
    os.environ["SCARPASOUN_ENV"] = "local"
    scarp_env = "local"

scarp_env = os.environ["SCARPASOUN_ENV"]
lambro_config = ReadConfig(env_type=scarp_env)
available_groups = lambro_config['scarp_groups']

def build_scarp_internal_header(user_group_header: list, ranking_groups: dict = {1: 'ift-scarp-admin', 2: 'ift-scarp-rw', 3: 'ift-scarp-ro'}) -> str:
    if isinstance(user_group_header, str):
        groups = user_group_header.split(",")
        groups = [group.strip() for group in groups if group.strip()]
    else:
        groups = user_group_header
    # Filter the list to include only items present in the ranking dictionary
    filtered_list = [item for item in groups if item in ranking_groups.values()]
    # If the filtered list is empty, there are no matching items
    if not filtered_list:
       return None    
    # Find the item with the highest priority
    highest_priority_group = min(filtered_list, key=lambda x: list(ranking_groups.values()).index(x))
    return highest_priority_group

class CustomAuthBackend(AuthenticationBackend):
    async def authenticate(self, request: Request):
        try:
            username = request.headers.get("X-Forwarded-Email", "")
            username = username.replace('@ucl.ac.uk', '')
            groups_raw = request.headers.get("X-Forwarded-Groups", "").split(",")
            groups = [trim_string(group, 'leading', action_regex='\\s+') for group in groups_raw]
        except KeyError:
            scarp_logger.error('Scarp CustomAuthBackend User not authenticated')

        groups = [group.strip() for group in groups if group.strip()]
        groups = build_scarp_internal_header(groups)

        if username and groups:
            # Create a SimpleUser instance with the username
            scarp_logger.info(f"User {username} started a session")
            user = SimpleUser(username)
            # Return the user and the authentication credentials
            return AuthCredentials(scopes=[groups]), user
        else:
            return None

def on_auth_error(request, exc):
    return JSONResponse({"error": str(exc)}, status_code=401)


class CheckPermissionsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        try:
            if isinstance(request.user, UnauthenticatedUser):                
                return await forbidden_page(request=request, exc=HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized, please log back in"))
                
            set_groups = set(request.auth.scopes)
            if not set_groups.intersection(available_groups):
                return await forbidden_page(request=request, exc=HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized, you are not part of the required groups"))                
            
            scarp_group = build_scarp_internal_header(user_group_header=request.headers.get("X-Forwarded-Groups", ""))
            if not scarp_group:
                return await forbidden_page(request=request, exc=HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized, you are not part of the required groups"))

            request.scope['headers'].append((b'X-scarp-Group', scarp_group.encode()))        
            response = await call_next(request)
            print(response.status_code)
            if response.status_code == 404:
                return await not_found(request=request, exc=HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="This page does not exist"))
            return response
        except HTTPException as hxp:
            if hxp.status_code == 404:
                return await not_found(request=request, exc=HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="This page does not exist"))
            if hxp.status_code == 403:
                return await forbidden_page(request=request, exc=HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access Denied"))
            raise
        except Exception as exc:
            print(f"Error as : {exc}")
            return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"error_message": "Internal Server Error"})