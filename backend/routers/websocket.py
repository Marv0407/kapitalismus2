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
        # Sende initialen State über den Manager
        await manager.send_personal_update(player_id, player)

        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            # --- Manuelles Sammeln ---
            if action == "gather_manual":
                resource_type = data.get("resource")
                p_state = await PlayerState.select_for_update().get(id=player_id)

                # Berechnet das gesamte Inventarvolumen
                total_resources = (
                    p_state.wood + p_state.stone + p_state.coal + p_state.iron_ore +
                    p_state.iron + p_state.steel + p_state.seed + p_state.fruit +
                    p_state.vegetable + p_state.livestock + p_state.meat +
                    p_state.grain + p_state.bread + p_state.wool + p_state.cotton +
                    p_state.fabric + p_state.clothes
                )

                # Nur hinzufügen, wenn noch Platz im globalen Lager ist
                if total_resources < p_state.max_storage:
                    if resource_type == "wood":
                        p_state.wood += 1
                    elif resource_type == "stone":
                        p_state.stone += 1
                    # Weitere Ressourcen für manuellen Abbau können hier bei Bedarf ergänzt werden

                    await p_state.save()
                    await manager.send_personal_update(player_id, p_state)

            elif action == "sell_wood":
                p_state = await PlayerState.select_for_update().get(id=player_id)
                if p_state.wood >= 10:
                    p_state.wood -= 10
                    p_state.gold += 5
                    await p_state.save()

                    await manager.send_personal_update(player_id, p_state)
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
