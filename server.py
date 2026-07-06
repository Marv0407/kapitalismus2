import asyncio
import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from tortoise.contrib.fastapi import register_tortoise
from pydantic import BaseModel

# Die Modelle aus der neuen Datei importieren
from models import User, PlayerState, Region, PlayerBuilding

app = FastAPI()

# -----------------------------------------------------------------------------
# DATENBANK KONFIGURATION (Hier deine Strato-Daten eintragen)
# -----------------------------------------------------------------------------
# DATABASE_CONFIG = {
#     "connections": {
#         "default": "mysql://dbu1489685:T4TqmjBNt!Lkh3D@database-5020858205.webspace-host.com:3306/dbs15866030"
#     },
#     "apps": {
#         "models": {
#             "models": ["models"],  # Verweist jetzt direkt auf die Datei models.py
#             "default_connection": "default",
#         }
#     }
# }

# -----------------------------------------------------------------------------
# DATENBANK KONFIGURATION (Lokal SQLite, auf dem VPS später MariaDB)
# -----------------------------------------------------------------------------
DATABASE_CONFIG = {
    "connections": {
        "default": "sqlite://db.sqlite3"  # Erstellt automatisch eine Datei im Projektordner
    },
    "apps": {
        "models": {
            "models": ["models"],
            "default_connection": "default",
        }
    }
}

# -----------------------------------------------------------------------------
# GAME LOGIC & NETWORKING
# -----------------------------------------------------------------------------
connected_players = {}



async def game_tick_loop():
    while True:
        await asyncio.sleep(5.0)
        try:
            players = await PlayerState.all()
            for player in players:
                player.wood += 2
                if player.wood > 50 and player.gold > 0:
                    player.gold -= 1
                await player.save()

                await send_player_update(player.id, player.gold, player.wood)

            # Nach jedem globalen Tick das Scoreboard für alle aktualisieren
            await broadcast_scoreboard()
        except Exception as e:
            print(f"Fehler im Game-Loop: {e}")


async def broadcast_scoreboard():
    """
    Sammelt alle Spieler, sortiert sie nach Gold,
    prüft den Online-Status und sendet das Scoreboard an ALLE Sockets.
    """
    try:
        # Alle Spieler inklusive zugehörigem User-Objekt laden (für den Namen)
        players = await PlayerState.all().prefetch_related("user")

        scoreboard_data = []
        for p in players:
            scoreboard_data.append({
                "username": p.user.username,
                "gold": p.gold,
                "online": p.id in connected_players
            })

        # Nach Gold absteigend sortieren
        scoreboard_data.sort(key=lambda x: x["gold"], reverse=True)

        payload = {
            "type": "scoreboard_update",
            "data": scoreboard_data
        }

        # Broadcast an wirklich jeden verbundenen Socket im System
        for player_id, sockets in connected_players.items():
            for ws in sockets:
                try:
                    await ws.send_json(payload)
                except Exception:
                    pass
    except Exception as e:
        print(f"Fehler beim Scoreboard-Broadcast: {e}")

async def send_player_update(player_id: int, gold: int, wood: int):
    if player_id in connected_players:
        payload = {"type": "resource_update", "data": {"gold": gold, "wood": wood}}
        for connection in connected_players[player_id]:
            try:
                await connection.send_json(payload)
            except Exception:
                pass

class AuthModel(BaseModel):
    username: str
    password: str

@app.post("/api/register")
async def register(data: AuthModel):
    #Prüfen ob existiert
    existing_user = await User.filter(username=data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Benutzername bereits vergeben")

    user = await User.create(username=data.username, password_hash=data.password)

    player = await PlayerState.create(user=user, gold=100, wood=0)
    region = await Region.create(coordinates_x=0, coordinates_y=0, region_type="Prototyp", player=player)
    await PlayerBuilding.create(player=player, region=region, building_type="holzfaeller", level=1, data={"efficiency": 1.0})

    return {"status": "success", "player_id": player.id}


@app.post("/api/login")
async def login(data: AuthModel):
    user = await User.filter(username=data.username).prefetch_related("player_state").first()
    if not user or user.password_hash != data.password:
        raise HTTPException(status_code=400, detail="Ungültige Zugangsdaten")

    return {"status": "success", "player_id": user.player_state.id}

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(game_tick_loop())


if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def get_index():
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    return FileResponse(html_path)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, player_id: int):
    await websocket.accept()

    if player_id not in connected_players:
        connected_players[player_id] = []
    connected_players[player_id].append(websocket)

    # Sobald jemand joint, aktualisiert sich für alle der Online-Status
    await broadcast_scoreboard()

    try:
        player = await PlayerState.get(id=player_id)
        await websocket.send_json({
            "type": "resource_update",
            "data": {"gold": player.gold, "wood": player.wood}
        })

        while True:
            data = await websocket.receive_json()
            if data.get("action") == "sell_wood":
                p_state = await PlayerState.select_for_update().get(id=player_id)
                if p_state.wood >= 10:
                    p_state.wood -= 10
                    p_state.gold += 5
                    await p_state.save()

                    await send_player_update(player_id, p_state.gold, p_state.wood)
                    # Direkt nach einem Handel das Scoreboard live updaten
                    await broadcast_scoreboard()

    except WebSocketDisconnect:
        connected_players[player_id].remove(websocket)
        if not connected_players[player_id]:
            del connected_players[player_id]
        # Wenn jemand geht, Scoreboard aktualisieren
        await broadcast_scoreboard()
    except Exception as e:
        print(f"Fehler im WebSocket für Spieler {player_id}: {e}")


async def send_player_update(player_id: int, gold: int, wood: int):
    """Hilfsfunktion, um gezielt Updates an einen Spieler zu senden."""
    if player_id in connected_players:
        payload = {"type": "resource_update", "data": {"gold": gold, "wood": wood}}
        for connection in connected_players[player_id]:
            try:
                await connection.send_json(payload)
            except Exception:
                pass


register_tortoise(
    app,
    config=DATABASE_CONFIG,
    generate_schemas=True,
    add_exception_handlers=True,
)
