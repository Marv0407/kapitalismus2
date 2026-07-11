import asyncio
from tortoise.transactions import in_transaction
from models import PlayerState, PlayerBuilding
from managers.connection_manager import manager


async def game_tick_loop():
    """Zentraler Loop für Produktion und Wachstum."""
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
                        if workers > 0:
                            if b.building_type == "holzfäller":
                                # 1 Arbeiter produziert 1 Holz alle 5 Sek (vereinfacht)
                                p_state.wood += workers
                            elif b.building_type == "steinbruch":
                                p_state.stone += workers
                                
                    # --- Bevölkerungswachstum (alle 60 Sekunden / 12 Ticks) ---
                    if tick_counter % 12 == 0:
                        if p_state.population < p_state.max_population:
                            p_state.population += 1
                            p_state.free_population += 1
                    
                    # Lagerlimit prüfen (nach Produktion)
                    total_res = (
                        p_state.wood + p_state.stone + p_state.coal + p_state.iron_ore +
                        p_state.iron + p_state.steel + p_state.seed + p_state.fruit +
                        p_state.vegetable + p_state.livestock + p_state.meat +
                        p_state.grain + p_state.bread + p_state.wool + p_state.cotton +
                        p_state.fabric + p_state.clothes
                    )
                    
                    if total_res > p_state.max_storage:
                        # Überschuss kappen (vereinfacht: Holz zuerst)
                        overfill = total_res - p_state.max_storage
                        p_state.wood = max(0, p_state.wood - overfill)

                    await p_state.save()
                    await manager.send_personal_update(p_state.id, p_state)

            await manager.broadcast_scoreboard()
            
        except Exception as e:
            print(f"Fehler im Game-Loop: {e}")
