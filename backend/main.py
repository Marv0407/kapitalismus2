import asyncio
import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from tortoise.contrib.fastapi import register_tortoise

from database import DATABASE_CONFIG
from routers import auth, websocket
from game_loop import game_tick_loop

app = FastAPI()

app.include_router(auth.router)
app.include_router(websocket.router)

@app.on_event("startup")
async def startup_event():
    """Startet asynchrone Hintergrundprozesse bei Serverstart."""
    asyncio.create_task(game_tick_loop())

if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def get_index():
    """Liefert die Einstiegsseite aus."""
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    return FileResponse(html_path)

if os.path.exists("frontend/src"):
    app.mount("/src", StaticFiles(directory="frontend/src"), name="src")
elif os.path.exists("src"):
    # Fallback, falls der src-Ordner direkt im Hauptverzeichnis liegt
    app.mount("/src", StaticFiles(directory="src"), name="src")

register_tortoise(
    app,
    config=DATABASE_CONFIG,
    generate_schemas=True,
    add_exception_handlers=True,
)
