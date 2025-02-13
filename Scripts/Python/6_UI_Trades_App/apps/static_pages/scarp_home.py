from starlette.responses import HTMLResponse, RedirectResponse
from starlette.authentication import UnauthenticatedUser

from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

# clyde home page
async def scarp_home(request):
    if isinstance(request.user, UnauthenticatedUser):
        return RedirectResponse(url="https://ucl.ac.uk/")
    else:        
        try:            
            html_scarp = templates.TemplateResponse("scarp.html", {"request": request, "username": request.user.display_name, "group": request.auth.scopes[0]})
        except Exception as exc:
            print(f"Exception found in : {exc}")        
        return html_scarp