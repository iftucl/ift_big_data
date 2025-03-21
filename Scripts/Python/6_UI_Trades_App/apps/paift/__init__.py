from starlette.applications import Starlette
from starlette.routing import Mount

from apps.paift.portfolio_analyser.main import paift_run_details
from apps.paift.trades_suspects.main import paift_trades_suspects

paift_rooter = Starlette(
    routes=[
        Mount("/paift_trades_monitor", paift_run_details),
        Mount("/paift_suspects_monitor", paift_trades_suspects),
    ]
)