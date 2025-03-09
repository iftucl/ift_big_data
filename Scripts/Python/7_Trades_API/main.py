import uvicorn
from app.server import app
from ift_global import ReadConfig
from ift_global.utils.set_env_var import set_env_variables
import os

from modules.utils.local_logger import lambro_logger

try:
    lambro_env = os.environ["LAMBRO_ENV"]
except KeyError:
    lambro_logger.warning(f"On start-up, 'LAMBRO_ENV' environment variable is not set. defaulting to 'dev'")
    os.environ["LAMBRO_ENV"] = "dev"
    lambro_env = "dev"

lambro_config = ReadConfig(env_type=lambro_env)

if lambro_env == "dev":
    set_env_variables(lambro_config["config"]["env_variables"], env_type=lambro_env, env_file=True, env_file_path="./")
else:
    set_env_variables(lambro_config["config"]["env_variables"], env_type=lambro_env)


if __name__ == "__main__":
    uvicorn.run(app=app, host="0.0.0.0", port=8010)

