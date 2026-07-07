import asyncio
import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from tortoise.contrib.fastapi import register_tortoise

from database import DATABASE_CONFIG
from routers import auth, websocket
from game_loop import game_tick_loop
from world_generator import generate_world_if_empty

app = FastAPI()

app.include_router(auth.router)
app.include_router(websocket.router)

@app.on_event("startup")
async def startup_event():
    """Startet asynchrone Hintergrundprozesse bei Serverstart."""
    await asyncio.sleep(1)
    await generate_world_if_empty(radius=5)
    asyncio.create_task(game_tick_loop())

if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def get_index():
    """Liefert die Einstiegsseite aus."""
    # Wechselt vom backend-Ordner eine Ebene nach oben und geht in den frontend-Ordner
    html_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")

    # Fallback, falls lokal gearbeitet wird und die Struktur flach ist
    if not os.path.exists(html_path):
        html_path = os.path.join(os.path.dirname(__file__), "index.html")

    return FileResponse(html_path)

# Bestimme das übergeordnete Projektverzeichnis (kapitalismus2)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Mounten des statischen CSS-Verzeichnisses
static_path = os.path.join(BASE_DIR, "frontend", "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")

# Mounten des Quellcode-Verzeichnisses für ES6-Module
src_path = os.path.join(BASE_DIR, "frontend", "src")
if os.path.exists(src_path):
    app.mount("/src", StaticFiles(directory=src_path), name="src")

register_tortoise(
    app,
    config=DATABASE_CONFIG,
    generate_schemas=True,
    add_exception_handlers=True,
)
