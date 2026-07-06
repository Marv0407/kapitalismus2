from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from managers.connection_manager import manager
from backend.models import PlayerState

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, player_id: int):
    """Verwaltet den Lebenszyklus und die eingehenden Nachrichten einer WebSocket-Verbindung."""
    await manager.connect(websocket, player_id)
    await manager.broadcast_scoreboard()

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

                    await manager.send_personal_update(player_id, p_state.gold, p_state.wood)
                    await manager.broadcast_scoreboard()

    except WebSocketDisconnect:
        manager.disconnect(websocket, player_id)
        await manager.broadcast_scoreboard()
