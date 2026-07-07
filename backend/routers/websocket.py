from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from managers.connection_manager import manager
from models import PlayerState, WorldHex
from world_generator import generate_local_sectors

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, player_id: int):
    """Verwaltet den Lebenszyklus und die eingehenden Nachrichten einer WebSocket-Verbindung."""
    await manager.connect(websocket, player_id)
    await manager.broadcast_scoreboard()
    await manager.send_overworld_map(player_id)
    await manager.send_map_update(player_id)

    try:
        player = await PlayerState.get(id=player_id)
        await websocket.send_json({
            "type": "resource_update",
            "data": {"gold": player.gold, "wood": player.wood}
        })

        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "sell_wood":
                p_state = await PlayerState.select_for_update().get(id=player_id)
                if p_state.wood >= 10:
                    p_state.wood -= 10
                    p_state.gold += 5
                    await p_state.save()

                    await manager.send_personal_update(player_id, p_state.gold, p_state.wood)
                    await manager.broadcast_scoreboard()

            elif action == "claim_hex":
                q = data.get("q")
                r = data.get("r")
                hex_field = await WorldHex.get_or_none(q=q, r=r, owner_id__isnull=True)

                if hex_field:
                    p_state = await PlayerState.get(id=player_id)
                    hex_field.owner = p_state
                    await hex_field.save()

                    await generate_local_sectors(p_state, hex_field.terrain)

                    await manager.send_overworld_map(player_id)
                    await manager.send_map_update(player_id)

    except WebSocketDisconnect:
        manager.disconnect(websocket, player_id)
        await manager.broadcast_scoreboard()
