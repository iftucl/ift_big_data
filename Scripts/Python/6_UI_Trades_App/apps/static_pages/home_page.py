from starlette.responses import RedirectResponse
from starlette.authentication import UnauthenticatedUser

from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

# Home page
async def homepage(request):
    if isinstance(request.user, UnauthenticatedUser):
        return RedirectResponse(url="https://ucl.ac.uk/")
    else:
        try:            
            html_home = templates.TemplateResponse("homepage.html", {"request": request, "username": request.user.display_name, "group": request.auth.scopes[0]})
        except Exception as exc:
            print(f"Exception found in : {exc}")
        return html_home