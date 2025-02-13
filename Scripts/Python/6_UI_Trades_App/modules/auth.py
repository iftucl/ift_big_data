from starlette.authentication import AuthenticationBackend, SimpleUser, AuthCredentials
from starlette.requests import Request
from ift_global.utils.string_utils import trim_string
from modules.local_logger import scarp_logger

class CustomAuthBackend(AuthenticationBackend):
    async def authenticate(self, request: Request):
        try:
            username = request.headers.get("X-Forwarded-Email")
            username = username.replace('@ucl.ac.uk', '')
            groups_raw = request.headers.get("X-Forwarded-Groups", "").split(",")
            groups = [trim_string(group, 'leading', action_regex='\\s+') for group in groups_raw]
        except KeyError:
            scarp_logger.error('Scarpasoun CustomAuthBackend User not authenticated')

        groups = [group.strip() for group in groups if group.strip()]

        if username and groups:
            # Create a SimpleUser instance with the username
            scarp_logger.info(f"User {username} started a session")
            user = SimpleUser(username)
            # Return the user and the authentication credentials
            return AuthCredentials(scopes=groups), user
        else:
            return None

__all__ = ['SimpleAuthBackend']