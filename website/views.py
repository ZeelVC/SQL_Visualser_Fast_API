from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="website/templates")

@router.get("/")
async def home(request: Request):
    return templates.TemplateResponse("base.html", {"request": request})