from tortoise import fields, models

class User(models.Model):
    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=50, unique=True)
    password_hash = fields.CharField(max_length=255)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "users"

class PlayerState(models.Model):
    id = fields.IntField(pk=True)
    user = fields.OneToOneField("models.User", related_name="player_state")

    # Personalisierung
    color = fields.CharField(max_length=7, default="#eb720f") # Hex-Farbe

    # Währungen und Metriken
    gold = fields.BigIntField(default=50)
    total_sales = fields.BigIntField(default=0)

    # Bevölkerung
    population = fields.IntField(default=0)
    max_population = fields.IntField(default=0)
    free_population = fields.IntField(default=0)

    # Ressourcen
    wood = fields.BigIntField(default=0)
    stone = fields.BigIntField(default=0)
    coal = fields.BigIntField(default=0)
    iron_ore = fields.BigIntField(default=0)
    iron = fields.BigIntField(default=0)
    steel = fields.BigIntField(default=0)

    seed = fields.BigIntField(default=0)
    fruit = fields.BigIntField(default=0)
    vegetable = fields.BigIntField(default=0)
    livestock = fields.BigIntField(default=0)
    meat = fields.BigIntField(default=0)
    grain = fields.BigIntField(default=0)
    bread = fields.BigIntField(default=0)

    wool = fields.BigIntField(default=0)
    cotton = fields.BigIntField(default=0)
    fabric = fields.BigIntField(default=0)
    clothes = fields.BigIntField(default=0)


    # Limits
    max_storage = fields.BigIntField(default=100)

    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "player_states"

class Region(models.Model):
    id = fields.IntField(pk=True)
    player = fields.ForeignKeyField("models.PlayerState", related_name="regions", null=True)
    coordinates_x = fields.IntField()
    coordinates_y = fields.IntField()
    region_type = fields.CharField(max_length=50)

    class Meta:
        table = "regions"

class PlayerBuilding(models.Model):
    id = fields.IntField(pk=True)
    player = fields.ForeignKeyField("models.PlayerState", related_name="buildings")
    region = fields.ForeignKeyField("models.Region", related_name="buildings")
    building_type = fields.CharField(max_length=50)
    level = fields.IntField(default=1)
    data = fields.JSONField(default=dict)

    class Meta:
        table = "player_buildings"

class WorldHex(models.Model):
    id = fields.IntField(pk=True)
    q = fields.IntField() # Hex-Koord (Spalte)
    r = fields.IntField() # hex-koord (Reihe)
    terrain = fields.CharField(max_length=50)
    owner = fields.ForeignKeyField("models.PlayerState", related_name="owned_hexes", null=True)

    class Meta:
        table = "world_hexes"

class MarketPrice(models.Model):
    id = fields.IntField(pk=True)
    resource_type = fields.CharField(max_length=50, unique=True)
    base_price = fields.FloatField()
    current_price = fields.FloatField()
    stock = fields.BigIntField(default=1000)

    class Meta:
        table = "market_prices"
