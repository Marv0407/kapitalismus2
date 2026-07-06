import asyncio
from models import PlayerState
from managers.connection_manager import manager


async def game_tick_loop():
    """Zentraler Loop, der zyklisch Ressourcen generiert und Kosten abzieht."""
    while True:
        await asyncio.sleep(5.0)
        try:
            players = await PlayerState.all()
            for player in players:
                player.wood += 2
                if player.wood > 50 and player.gold > 0:
                    player.gold -= 1
                await player.save()

                await manager.send_personal_update(player.id, player.gold, player.wood)

            await manager.broadcast_scoreboard()
        except Exception as e:
            print(f"Fehler im Game-Loop: {e}")
