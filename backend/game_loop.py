import asyncio
from models import PlayerState
from managers.connection_manager import manager


async def game_tick_loop():
    """Zentraler Loop, der gerade nix tut."""
    while True:
        await asyncio.sleep(5.0)
        try:
            players = await PlayerState.all()
            for player in players:
                print("Online Players:" + str(player))
                await player.save()

                await manager.send_personal_update(player.id, player)

            await manager.broadcast_scoreboard()
        except Exception as e:
            print(f"Fehler im Game-Loop: {e}")
