from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from tortoise.exceptions import DoesNotExist
from tortoise.transactions import in_transaction
from managers.connection_manager import manager
from models import PlayerState, WorldHex, PlayerBuilding, Region
from world_generator import generate_local_sectors

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, player_id: int):
    """
        Verwaltet den Lebenszyklus und die eingehenden Nachrichten einer WebSocket-Verbindung.
        Prueft die Existenz des Spielers, bevor die Verbindung vollstaendig geoeffnet wird.
        """
    await manager.connect(websocket, player_id)

    try:
        player = await PlayerState.get(id=player_id)
    except DoesNotExist:
        manager.disconnect(websocket, player_id)
        await websocket.close(code=1008)
        return

    await manager.broadcast_scoreboard()
    await manager.send_overworld_map(player_id)
    await manager.send_map_update(player_id)

    try:
        await manager.send_personal_update(player_id, player)

        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "gather_manual":
                async with in_transaction():
                    p_state = await PlayerState.select_for_update().get(id=player_id)
                    
                    total_resources = (
                        p_state.wood + p_state.stone + p_state.coal + p_state.iron_ore +
                        p_state.iron + p_state.steel + p_state.seed + p_state.fruit +
                        p_state.vegetable + p_state.livestock + p_state.meat +
                        p_state.grain + p_state.bread + p_state.wool + p_state.cotton +
                        p_state.fabric + p_state.clothes
                    )

                    if total_resources < p_state.max_storage:
                        resource_type = data.get("resource")
                        if resource_type == "wood":
                            p_state.wood += 1
                        elif resource_type == "stone":
                            p_state.stone += 1

                        await p_state.save()
                        await manager.send_personal_update(player_id, p_state)

            elif action == "sell_wood":
                async with in_transaction():
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
                
                async with in_transaction():
                    p_state = await PlayerState.select_for_update().get(id=player_id)
                    existing_cities = await WorldHex.filter(owner=p_state).count()
                    
                    cost = 0 if existing_cities == 0 else 1000
                    
                    if p_state.gold < cost:
                        await websocket.send_json({"type": "error", "message": f"Nicht genug Gold! Kosten: {cost} G"})
                        continue

                    hex_field = await WorldHex.select_for_update().get_or_none(q=q, r=r, owner_id__isnull=True)
                    if hex_field:
                        p_state.gold -= cost
                        await p_state.save()
                        
                        hex_field.owner = p_state
                        await hex_field.save()

                        await generate_local_sectors(p_state, hex_field.terrain)

                        await manager.send_overworld_map(player_id)
                        await manager.send_map_update(player_id)
                        await manager.send_personal_update(player_id, p_state)

            elif action == "assign_workers":
                building_id = data.get("building_id")
                amount = data.get("amount", 1) # +1 oder -1
                
                async with in_transaction():
                    building = await PlayerBuilding.select_for_update().get_or_none(id=building_id, player_id=player_id)
                    p_state = await PlayerState.select_for_update().get(id=player_id)
                    
                    if building and p_state:
                        current_workers = building.data.get("workers", 0)
                        max_workers = building.data.get("max_workers", 5)
                        
                        if amount > 0: # Zuweisen
                            if p_state.free_population >= amount and current_workers + amount <= max_workers:
                                building.data["workers"] = current_workers + amount
                                p_state.free_population -= amount
                            else:
                                await websocket.send_json({"type": "error", "message": "Nicht genug freie Einwohner oder Limit erreicht!"})
                                continue
                        else: # Abziehen
                            if current_workers + amount >= 0:
                                building.data["workers"] = current_workers + amount
                                p_state.free_population -= amount # amount ist negativ, also +|amount|
                            else:
                                continue
                                
                        await building.save()
                        await p_state.save()
                        
                        await manager.send_map_update(player_id)
                        await manager.send_personal_update(player_id, p_state)

    except WebSocketDisconnect:
        manager.disconnect(websocket, player_id)
        await manager.broadcast_scoreboard()
