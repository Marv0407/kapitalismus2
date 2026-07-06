import asyncio
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from tortoise.contrib.fastapi import register_tortoise

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
active_connections = []


async def game_tick_loop():
    while True:
        await asyncio.sleep(5.0)

        # Versuche alle Spieler zu laden (Fehlermeldung abfangen, falls DB-Verbindung scheitert)
        try:
            players = await PlayerState.all()
            for player in players:
                player.wood += 2
                if player.wood > 50 and player.gold > 0:
                    player.gold -= 1

                await player.save()

                payload = {
                    "type": "resource_update",
                    "data": {
                        "gold": player.gold,
                        "wood": player.wood
                    }
                }

                for connection in active_connections:
                    try:
                        await connection.send_json(payload)
                    except Exception:
                        pass
        except Exception as e:
            print(f"Fehler im Game-Loop (Möglicherweise Verbindungsfehler zu Strato): {e}")


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
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)

    try:
        player = await PlayerState.first()
        if not player:
            dummy_user = await User.create(username="Prototyp_Spieler", password_hash="dummy")
            player = await PlayerState.create(user=dummy_user, gold=100, wood=0)
            region = await Region.create(coordinates_x=0, coordinates_y=0, region_type="Küste", player=player)
            await PlayerBuilding.create(player=player, region=region, building_type="holzfaeller", level=1,
                                        data={"efficiency": 1.0})

        await websocket.send_json({
            "type": "resource_update",
            "data": {"gold": player.gold, "wood": player.wood}
        })

        while True:
            data = await websocket.receive_json()
            if data.get("action") == "sell_wood":
                p_state = await PlayerState.select_for_update().get(id=player.id)
                if p_state.wood >= 10:
                    p_state.wood -= 10
                    p_state.gold += 5
                    await p_state.save()

    except WebSocketDisconnect:
        active_connections.remove(websocket)
    except Exception as e:
        print(f"Fehler im WebSocket-Endpoint: {e}")


register_tortoise(
    app,
    config=DATABASE_CONFIG,
    generate_schemas=True,
    add_exception_handlers=True,
)
