from fastapi.templating import Jinja2Templates

from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import HTMLResponse

# Set up Jinja2Templates
templates = Jinja2Templates(directory="templates")

# Define the custom 404 handler
async def not_found(request: Request, exc: str):
    context = {'request': request, 'error_message': exc}
    return templates.TemplateResponse("404.html", context=context)

# Define the custom 403 handler
async def forbidden_page(request: Request, exc: str):
    context = {'request': request, 'error_message': exc}
    return templates.TemplateResponse("403.html", context=context)

# Register custom exception handlers
custom_exception_handlers = {
    404: not_found,
    403: forbidden_page,
}