import random
from models import WorldHex, Region, PlayerBuilding

async def generate_world_if_empty(radius: int = 5):
    """
        Generiert eine hexagonale Weltkarte basierend auf axialen Koordinaten (q, r).
        Wenn bereits Hexfelder existieren, wird der Prozess übersprungen.
        """
    existing_hexes = await WorldHex.all().count()
    if existing_hexes > 0:
        print(f"Weltkarte existiert bereits mit {existing_hexes} Sektoren.")
        return

    print("Generiere neue Overworld...")
    terrains = ["Wald", "Wald", "Ebene", "Ebene", "Ebene", "Gebirge", "Küste"]

    #Generierung eines hexagonalen Grids in einem bestimmten Radius
    hex_list = []
    for q in range(-radius, radius + 1):
        for r in range(max(-radius, -q - radius), min(radius, -q + radius) + 1):
            terrain = random.choice(terrains)
            hex_list.append(WorldHex(q=q, r=r, terrain=terrain))

    await WorldHex.bulk_create(hex_list)
    print(f"Weltkarte mit {len(hex_list)} Hexfelder erfolgreich generiert.")

async def generate_local_sectors(player, base_terrain: str):
    """Generiert ein lokales 5x5 Sektoren-Grid für einen Spieler.
    Die Terrainverteilung basiert primär auf dem Biom des beanspruchten Welt-Hexfelds"""

    terrain_weights = {
        "Wald": ["Wald", "Wald", "Wald", "Ebene", "Küste"],
        "Ebene": ["Ebene", "Ebene", "Ebene", "Wald", "Küste"],
        "Gebirge": ["Gebirge", "Gebirge", "Gebirge", "Ebene", "Wald"],
        "Küste": ["Küste", "Küste", "Küste", "Ebene", "Meer"]
    }

    choices = terrain_weights.get(base_terrain, ["Ebene"])
    regions = []

    for y in range(-2 , 3):
        for x in range(-2, 3):
            t = random.choice(choices)
            regions.append(Region(coordinates_x=x, coordinates_y=y, region_type=t, player=player))

    await Region.bulk_create(regions)

    center_region = await Region.get(player=player, coordinates_x=0, coordinates_y=0)
    await PlayerBuilding.create(
        player=player,
        region=center_region,
        building_type="holzfäller",
        level=1,
        data={"efficiency": 1.0}
    )
