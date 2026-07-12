"""
Zentrale Konfigurationsdatei für Spielmechaniken und Balancing-Werte.
"""

BUILDING_COSTS = {
    "holzfäller": {"wood": 20, "stone": 5},
    "steinbruch": {"wood": 30, "stone": 10},
    "wohnhaus": {"wood": 25, "stone": 15},
    "lagerhaus": {"wood": 50, "stone": 30}
}

BUILDING_MAINTENANCE = {
    "holzfäller": 1,
    "steinbruch": 2,
    "wohnhaus": 0,
    "lagerhaus": 0
}

BUILDING_EFFICIENCY = {
    "holzfäller_biome": "Wald",
    "steinbruch_biome": "Gebirge",
    "bonus_multiplier": 1.5
}

POPULATION_SETTINGS = {
    "wohnhaus_max_pop": 5,
    "wohnhaus_start_pop": 2,
    "happiness_migration_high": 50,
    "happiness_migration_low": 20,
    "tax_happiness_bonus_0": 5,
    "tax_happiness_bonus_1": 1,
    "tax_happiness_penalty_multiplier": 3
}

STORAGE_SETTINGS = {
    "lagerhaus_capacity": 250
}

MARKET_SETTINGS = {
    "initial_stock": 1000,
    "initial_base_price": 4.0,
    "consumption_rate": 0.05,
    "max_price_multiplier": 10
}
