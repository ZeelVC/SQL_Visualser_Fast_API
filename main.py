import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from website.auth import router as auth_router
from website.views import router as views_router

app = FastAPI()

# Mount static files
#app.mount("/static", StaticFiles(directory="website/static"), name="static")

# Include routers
app.include_router(views_router)
app.include_router(auth_router)

# Templates
#templates = Jinja2Templates(directory="website/templates")
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "website", "templates"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)