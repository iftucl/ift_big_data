from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.responses import HTMLResponse
from starlette.middleware import Middleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.exceptions import ExceptionMiddleware
import uvicorn
from fastapi.staticfiles import StaticFiles
from ift_global.utils.set_env_var import set_env_variables
from ift_global import ReadConfig
import os

from modules.middleware_helper import CustomAuthBackend, AuthenticationMiddleware, CheckPermissionsMiddleware
from modules.exception_abstraction import custom_exception_handlers

from apps.paift import paift_rooter
from apps.static_pages import static_pages_rooter
from modules.local_logger import scarp_logger


# Define the proxy function
# Starlette app
app = Starlette(
    debug=False,
    routes=[        
        Mount("/scarp/paift", paift_rooter),
        Mount("/static", StaticFiles(directory="www"), name="static"),
        Mount("/", static_pages_rooter),
    ],
    middleware=[
        Middleware(TrustedHostMiddleware, allowed_hosts=["*"]),
        Middleware(SessionMiddleware, secret_key=os.getenv("scarp_TOKEN_SECRET", "")),
        Middleware(AuthenticationMiddleware, backend=CustomAuthBackend()),
        Middleware(CheckPermissionsMiddleware),
        Middleware(ExceptionMiddleware),
    ],
    exception_handlers=custom_exception_handlers,
)


if __name__ == "__main__":
    try:
        clyde_env = os.environ["scarp_ENV"]
    except KeyError:
        scarp_logger.warning(f"On start-up, 'scarp_ENV' env variable is not set. Defaulting to local env")    
        os.environ["scarp_ENV"] = "local"
        clyde_env = "local"

    clyde_config = ReadConfig(env_type=clyde_env)
    if clyde_env == "local":
        set_env_variables(clyde_config['env_variables'], 
                          env_type=clyde_env, env_file=True, env_file_path='./')
    else:
        set_env_variables(clyde_config['env_variables'], env_type=clyde_env)

    available_groups = set(scarp_config['scarp_groups'])

    uvicorn.run(app, host="0.0.0.0", port=8100)