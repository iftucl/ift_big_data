from starlette.applications import Starlette
from starlette.routing import Mount

from apps.paift.portfolio_analyser.main import paift_run_details

paift_rooter = Starlette(
    routes=[
        Mount("/paift_runids", paift_run_details),
    ]
)