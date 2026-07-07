from fastapi import WebSocket
# models! nicht backend.models, weil sonst der pfad ins Leere geht beim server start :P
from models import PlayerState, Region, WorldHex


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, player_id: int):
        """Akzeptiert eine WebSocket-Verbindung und ordnet sie der Spieler-ID zu."""
        await websocket.accept()
        if player_id not in self.active_connections:
            self.active_connections[player_id] = []
        self.active_connections[player_id].append(websocket)

    def disconnect(self, websocket: WebSocket, player_id: int):
        """Entfernt eine getrennte WebSocket-Verbindung aus der aktiven Liste."""
        if player_id in self.active_connections:
            self.active_connections[player_id].remove(websocket)
            if not self.active_connections[player_id]:
                del self.active_connections[player_id]

    async def send_personal_update(self, player_id: int, gold: int, wood: int):
        """Sendet ein Ressourcen-Update an alle aktiven Verbindungen eines spezifischen Spielers."""
        if player_id in self.active_connections:
            payload = {"type": "resource_update", "data": {"gold": gold, "wood": wood}}
            for connection in self.active_connections[player_id]:
                try:
                    await connection.send_json(payload)
                except Exception:
                    pass

    async def broadcast_scoreboard(self):
        """Ermittelt den aktuellen Goldstand aller Spieler und sendet die Rangliste an alle verbundenen Clients."""
        try:
            players = await PlayerState.all().prefetch_related("user")
            scoreboard_data = []

            for p in players:
                scoreboard_data.append({
                    "username": p.user.username,
                    "gold": p.gold,
                    "online": p.id in self.active_connections
                })

            scoreboard_data.sort(key=lambda x: x["gold"], reverse=True)
            payload = {"type": "scoreboard_update", "data": scoreboard_data}

            for player_id, sockets in self.active_connections.items():
                for ws in sockets:
                    try:
                        await ws.send_json(payload)
                    except Exception:
                        pass
        except Exception as e:
            print(f"Fehler beim Scoreboard-Broadcast: {e}")

    async def send_map_update(self,player_id: int):
        """Lädt alle Sektoren und Gebäude eines SPielers und sendet diese an den Client"""
        if player_id in self.active_connections:
            regions = await Region.filter(player_id=player_id).prefetch_related("buildings")

            map_data = []
            for r in regions:
                building = r.buildings[0] if r.buildings else None
                map_data.append({
                    "x": r.coordinates_x,
                    "y": r.coordinates_y,
                    "type": r.region_type,
                    "building": building.building_type if building else None,
                    "level": building.level if building else 0,
                    # Module wie gebäudeverbesserungen, slots werden mit level freigeschaltet oderso
                })

            payload = {"type": "map_update", "data": map_data}
            for connection in self.active_connections[player_id]:
                try:
                    await connection.send_json(payload)
                except Exception:
                    pass

    async def send_overworld_map(self, player_id: int):
        """Lädt alle Weltkarte-Hexfelder und sendet diese an den Vlient."""
        if player_id in self.active_connections:
            hexes = await WorldHex.all().prefetch_related("owner")

            map_data = []
            for h in hexes:
                map_data.append({
                    "id": h.id,
                    "q": h.q,
                    "r": h.r,
                    "terrain": h.terrain,
                    "owner_id": h.owner.id if h.owner else None
                })

            payload = {"type": "overworld_update", "data": map_data}
            for connection in self.active_connections[player_id]:
                try:
                    await connection.send_json(payload)
                except Exception:
                    pass

manager = ConnectionManager()
