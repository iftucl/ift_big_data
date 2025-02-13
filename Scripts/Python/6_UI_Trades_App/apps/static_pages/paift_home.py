from starlette.responses import RedirectResponse
from starlette.authentication import UnauthenticatedUser

from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

# paift home page
async def paift_home(request):
    if isinstance(request.user, UnauthenticatedUser):
        return RedirectResponse(url="https://ucl.ac.uk/")
    else:
        try:            
            html_paift = templates.TemplateResponse("paift.html", {"request": request, "username": request.user.display_name, "group": request.auth.scopes[0]})
        except Exception as exc:
            print(f"Exception found in : {exc}")        
        return html_paift