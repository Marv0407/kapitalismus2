from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from managers.connection_manager import manager
from models import PlayerState, WorldHex, PlayerBuilding, Region, MarketPrice
from tortoise.exceptions import DoesNotExist
from tortoise.transactions import in_transaction
from world_generator import generate_local_sectors
import asyncio

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
                        p_state.wood + p_state.stone + p_state.coal + p_state.iron_ore + p_state.iron + p_state.steel + p_state.seed + p_state.fruit + p_state.vegetable + p_state.livestock + p_state.meat + p_state.grain + p_state.bread + p_state.wool + p_state.cotton + p_state.fabric + p_state.clothes)

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
                amount = data.get("amount", 1)  # +1 oder -1

                async with in_transaction():
                    building = await PlayerBuilding.select_for_update().get_or_none(id=building_id, player_id=player_id)
                    p_state = await PlayerState.select_for_update().get(id=player_id)

                    if building and p_state:
                        current_workers = building.data.get("workers", 0)
                        max_workers = building.data.get("max_workers", 5)

                        if amount > 0:  # Zuweisen
                            if p_state.free_population >= amount and current_workers + amount <= max_workers:
                                building.data["workers"] = current_workers + amount
                                p_state.free_population -= amount
                            else:
                                await websocket.send_json(
                                    {"type": "error", "message": "Nicht genug freie Einwohner oder Limit erreicht!"})
                                continue
                        else:  # Abziehen
                            if current_workers + amount >= 0:
                                building.data["workers"] = current_workers + amount
                                p_state.free_population -= amount  # amount ist negativ, also +|amount|
                            else:
                                continue

                        await building.save()
                        await p_state.save()

                        await manager.send_map_update(player_id)
                        await manager.send_personal_update(player_id, p_state)

            # --- Gebäude bauen ---
            elif action == "build_building":
                region_id = int(data.get("region_id"))  # Die ID der geklickten lokalen Grid-Kachel
                b_type = data.get("building_type")  # 'holzfaeller', 'steingrube', 'wohnhaus'

                costs = {"holzfaeller": {"wood": 20, "stone": 5}, "steingrube": {"wood": 30, "stone": 10},
                         "wohnhaus": {"wood": 25, "stone": 15}}

                if b_type not in costs:
                    continue

                p_state = await PlayerState.select_for_update().get(id=player_id)

                # Validierung: Gehört die Region/Kachel wirklich dem Spieler?
                region = await Region.get_or_none(id=region_id, player=p_state)
                if not region:
                    continue

                # Validierung: Ist die Kachel bereits bebaut?
                already_built = await PlayerBuilding.filter(region=region).exists()
                if already_built:
                    continue

                # Validierung: Ressourcenprüfung im Backend
                req = costs[b_type]
                if p_state.wood >= req["wood"] and p_state.stone >= req["stone"]:
                    p_state.wood -= req["wood"]
                    p_state.stone -= req["stone"]

                    # Biom-Effizienz ermitteln
                    eff = 1.0
                    if b_type == "holzfaeller" and region.region_type == "Wald":
                        eff = 1.5
                    elif b_type == "steingrube" and region.region_type == "Gebirge":
                        eff = 1.5

                    # Wohnhaus-Effekt: Erhöht das Bevölkerungslimit
                    if b_type == "wohnhaus":
                        p_state.max_population += 5
                        p_state.free_population += 5

                    await p_state.save(update_fields=["wood", "stone", "max_population", "free_population"])

                    # Speichern der Effizienz im bestehenden JSONField
                    await PlayerBuilding.create(player=p_state, region=region, building_type=b_type, level=1,
                        data={"workers": 0, "efficiency": eff}  # Setzt beide Werte initial fest
                    )

                    await manager.send_personal_update(player_id, p_state)
                    await manager.send_map_update(player_id)

            # --- Ressourcen an fahrende Händler (NPC) verkaufen ---
            elif action == "sell_to_npc":
                resource_type = data.get("resource")
                amount = int(data.get("amount", 0))

                if amount <= 0:
                    continue

                p_state = await PlayerState.select_for_update().get(id=player_id)
                current_stock = getattr(p_state, resource_type, 0)

                if current_stock >= amount:
                    market = await MarketPrice.select_for_update().get_or_none(resource_type=resource_type)
                    if not market:
                        continue

                    # Dynamischer Preis-Algorithmus
                    price_per_unit = market.base_price * (1000 / max(market.stock, 1))
                    price_per_unit = max(1.0, min(price_per_unit, market.base_price * 3))

                    total_payout = int(price_per_unit * amount)

                    setattr(p_state, resource_type, current_stock - amount)
                    p_state.gold += total_payout
                    p_state.total_sales += total_payout
                    await p_state.save(update_fields=[resource_type, "gold", "total_sales"])

                    market.stock += amount
                    market.current_price = market.base_price * (1000 / max(market.stock, 1))
                    await market.save(update_fields=["stock", "current_price"])

                    await manager.send_personal_update(player_id, p_state)
                    await manager.broadcast_scoreboard()

                # ==========================================  #   DEVELOPER TOOLS & CHEAT PANEL  # ==========================================
            elif action == "dev_cheat_resources":
                p_state = await PlayerState.select_for_update().get(id=player_id)

                # Maximiert alle Grundressourcen für Testzwecke
                p_state.gold += 5000
                p_state.wood = min(p_state.max_storage, p_state.wood + 100)
                p_state.stone = min(p_state.max_storage, p_state.stone + 100)
                p_state.max_population += 20
                p_state.free_population += 20

                await p_state.save()
                await manager.send_personal_update(player_id, p_state)
                print(f"[DEV] Spieler {player_id} hat Ressourcen gecheatet.")

            elif action == "dev_execute_code":
                code_to_eval = data.get("code", "").strip()
                print(f"[DEV] Führe Live-Code aus:\n{code_to_eval}")

                local_context = {
                    "PlayerState": PlayerState,
                    "manager": manager,
                    "player_id": player_id,
                    "asyncio": asyncio
                }

                try:
                    # 1. Einzeiler ohne 'await' direkt auswerten
                    if "\n" not in code_to_eval and not code_to_eval.startswith("await"):
                        result = eval(code_to_eval, globals(), local_context)
                        out_msg = f"Ergebnis: {result}"
                    else:
                        # 2. Mehrzeiliger asynchroner Code sicher verpacken und einrücken
                        # Jede Zeile wird sauber um 4 Leerzeichen eingerückt, Leerzeilen werden ignoriert
                        indented_code = "\n".join(f"    {line}" for line in code_to_eval.splitlines() if line.strip())
                        wrapper_code = f"async def _dev_exec():\n{indented_code}"

                        # Kompilieren und im Kontext registrieren
                        compiled_code = compile(wrapper_code, "<dev_console>", "exec")
                        exec(compiled_code, globals(), local_context)

                        # Funktion ausführen
                        func = local_context["_dev_exec"]
                        await func()
                        out_msg = "Code erfolgreich ausgeführt."

                except Exception as e:
                    # Der alles entscheidende Failsafe: Fehler ausgeben, aber die Schleife NICHT abbrechen!
                    out_msg = f"Fehler bei Code-Ausführung: {e}"
                    print(f"[DEV - ERROR] Live-Code Fehler: {e}")

                # Feedback an das Dev-Panel senden, Verbindung bleibt durch das 'try-except' stabil
                await websocket.send_json({
                    "type": "dev_console_output",
                    "data": {"message": out_msg}
                })
            elif action == "toggle_export":
                resource_type = data.get("resource")
                is_enabled = bool(data.get("enabled", False))

                print(
                    f"[DEBUG - WS] toggle_export empfangen: Spieler={player_id}, Ressource={resource_type}, Status={is_enabled}")

                p_state = await PlayerState.select_for_update().get(id=player_id)

                if not isinstance(p_state.export_settings, dict):
                    print(f"[DEBUG - WS] export_settings war kein dict, initialisiere neu.")
                    p_state.export_settings = {}

                p_state.export_settings[resource_type] = is_enabled
                await p_state.save(update_fields=["export_settings"])

                print(f"[DEBUG - WS] export_settings erfolgreich gespeichert: {p_state.export_settings}")
                await manager.send_personal_update(player_id, p_state)

            elif action == "sell_to_npc":
                resource_type = data.get("resource")
                amount = int(data.get("amount", 0))

                print(
                    f"[DEBUG - WS] sell_to_npc empfangen: Spieler={player_id}, Ressource={resource_type}, Menge={amount}")

                if amount <= 0:
                    print(f"[DEBUG - WS] Abbruch: Menge <= 0")
                    continue

    except WebSocketDisconnect:
        manager.disconnect(websocket, player_id)
        await manager.broadcast_scoreboard()
