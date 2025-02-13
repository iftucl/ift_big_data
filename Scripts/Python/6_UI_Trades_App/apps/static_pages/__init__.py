from apps.static_pages.home_page import homepage
from apps.static_pages.scarp_home import scarp_home
from apps.static_pages.paift_home import paift_home
from fastapi.staticfiles import StaticFiles

from starlette.applications import Starlette
from starlette.routing import Route, Mount

static_pages_rooter = Starlette(
    routes=[
        Route("/", homepage),
        Route("/scarp", scarp_home),
        Route("/scarp/paift", paift_home),
    ]
)