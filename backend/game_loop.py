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
                from models import MarketPrice
                markets = await MarketPrice.all()
                market_dict = {m.resource_type: m for m in markets}
                prices_changed = False

                # 1. Automatischer Export der Spieler
                for player in players:
                    p_state = await PlayerState.select_for_update().get(id=player.id)
                    export_settings = p_state.export_settings if isinstance(p_state.export_settings, dict) else {}

                    player_updated = False
                    for res_type, enabled in export_settings.items():
                        if enabled:
                            current_stock = getattr(p_state, res_type, 0)
                            # Exportiert immer in 10er-Blöcken, wenn genug da ist
                            if current_stock >= 10:
                                market = market_dict.get(res_type)
                                if not market:
                                    continue

                                # Dynamische Preisberechnung
                                price_per_unit = market.base_price * (1000 / max(market.stock, 1))
                                price_per_unit = max(1.0, min(price_per_unit, market.base_price * 3))
                                total_payout = int(price_per_unit * 10)

                                # Ressourcen abziehen, Gold hinzufügen
                                setattr(p_state, res_type, current_stock - 10)
                                p_state.gold += total_payout
                                p_state.total_sales += total_payout

                                # Markt sättigen
                                market.stock += 10
                                market.current_price = market.base_price * (1000 / max(market.stock, 1))
                                await market.save(update_fields=["stock", "current_price"])

                                player_updated = True
                                prices_changed = True

                    if player_updated:
                        await p_state.save()
                        await manager.send_personal_update(p_state.id, p_state)

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
