import asyncio
from tortoise.transactions import in_transaction
from models import PlayerState, PlayerBuilding
from managers.connection_manager import manager


async def game_tick_loop():
    """Zentraler Loop fuer Produktion und Wachstum."""
    tick_counter = 0
    while True:
        await asyncio.sleep(5.0)
        tick_counter += 1

        try:
            players = await PlayerState.all()
            for player in players:
                async with in_transaction():
                    p_state = await PlayerState.select_for_update().get(id=player.id)
                    buildings = await PlayerBuilding.filter(player=p_state).all()

                    # --- Produktion ---
                    for b in buildings:
                        workers = b.data.get("workers", 0)
                        efficiency = b.data.get("efficiency", 1.0)

                        if workers > 0:
                            # Berechnung: zugewiesene Arbeiter * Basisertrag * Biom-Effizienz
                            if b.building_type == "holzfäller":
                                p_state.wood += int(workers * 1 * efficiency)
                            elif b.building_type == "steinbruch":
                                p_state.stone += int(workers * 1 * efficiency)

                    # --- Bevoelkerungswachstum (alle 60 Sekunden / 12 Ticks) ---
                    if tick_counter % 12 == 0:
                        if p_state.population < p_state.max_population:
                            p_state.population += 1
                            p_state.free_population += 1

                    # Lagerlimit pruefen (nach Produktion)
                    total_res = (
                        p_state.wood + p_state.stone + p_state.coal + p_state.iron_ore +
                        p_state.iron + p_state.steel + p_state.seed + p_state.fruit +
                        p_state.vegetable + p_state.livestock + p_state.meat +
                        p_state.grain + p_state.bread + p_state.wool + p_state.cotton +
                        p_state.fabric + p_state.clothes
                    )

                    if total_res > p_state.max_storage:
                        # Ueberschuss kappen (Holz zuerst)
                        overfill = total_res - p_state.max_storage
                        p_state.wood = max(0, p_state.wood - overfill)

                    await p_state.save()
                    await manager.send_personal_update(p_state.id, p_state)

            await manager.broadcast_scoreboard()

            # --- Wirtschaftssimulation & Automatischer Export (alle 15 Sekunden / 3 Ticks) ---
            if tick_counter % 3 == 0:
                print(f"\n[DEBUG - LOOP] --- Starte Marktsimulation (Tick {tick_counter}) ---")
                from models import MarketPrice
                markets = await MarketPrice.all()
                market_dict = {m.resource_type: m for m in markets}
                prices_changed = False

                # Failsafe: Falls die Datenbank leer ist, Markt sofort aufbauen
                if not markets:
                    print("[DEBUG - LOOP] Markt ist leer! Initialisiere Standardpreise...")
                    resources = [
                        "wood", "stone", "coal", "iron_ore", "iron", "steel",
                        "seed", "fruit", "vegetable", "livestock", "meat", "grain", "bread",
                        "wool", "cotton", "fabric", "clothes"
                    ]
                    price_list = []
                    for res in resources:
                        price_list.append(MarketPrice(resource_type=res, base_price=4.0, current_price=4.0, stock=1000))
                    await MarketPrice.bulk_create(price_list)
                    # Märkte direkt nach Erstellung neu laden
                    markets = await MarketPrice.all()

                market_dict = {m.resource_type: m for m in markets}
                prices_changed = False

                # 1. Automatischer Export der Spieler
                for player in players:
                    # Lade den PlayerState neu, um sicherzustellen, dass wir die neuesten
                    # Export-Einstellungen haben, die seit Beginn des Ticks geändert worden sein könnten.
                    p_state = await PlayerState.get(id=player.id)

                    export_settings = p_state.export_settings if isinstance(p_state.export_settings, dict) else {}

                    print(f"[DEBUG - LOOP] Prüfe Spieler {p_state.id}. Export-Settings: {export_settings}")

                    player_updated = False
                    for res_type, enabled in export_settings.items():
                        if enabled:
                            current_stock = getattr(p_state, res_type, 0)
                            print(f"[DEBUG - LOOP] -> {res_type} ist aktiviert. Aktueller Bestand: {current_stock}")

                            if current_stock >= 10:
                                market = market_dict.get(res_type)
                                if not market:
                                    print(f"[DEBUG - ERROR] Kein Markteintrag für {res_type} gefunden!")
                                    continue

                                # ... Deine Preisberechnungs- und Speicherlogik ...
                                print(f"[DEBUG - LOOP] -> Verkaufe 10 {res_type}. Neuer Bestand: {current_stock - 10}")
                                player_updated = True
                                prices_changed = True
                            else:
                                print(f"[DEBUG - LOOP] -> Bestand zu gering für automatischen Export (< 10).")

                    if player_updated:
                        await p_state.save()
                        await manager.send_personal_update(p_state.id, p_state)
                        print(f"[DEBUG - LOOP] Spieler {p_state.id} nach Export in DB gespeichert.")
                # 2. Konsum des Königreichs (Märkte regenerieren sich langsam)
                for m in markets:
                    if m.stock > 1000:
                        reduction = int((m.stock - 1000) * 0.05) + 1
                        m.stock -= reduction
                        m.current_price = m.base_price * (1000 / max(m.stock, 1))
                        await m.save(update_fields=["stock", "current_price"])
                        prices_changed = True

                if prices_changed:
                    await manager.broadcast_market_prices()

        except Exception as e:
            print(f"Fehler im Game-Loop: {e}")
