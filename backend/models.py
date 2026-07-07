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
    gold = fields.BigIntField(default=100)
    wood = fields.BigIntField(default=0)
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
