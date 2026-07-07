from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from models import User, PlayerState, Region, PlayerBuilding

router = APIRouter(prefix="/api", tags=["auth"])


class AuthModel(BaseModel):
    username: str
    password: str


@router.post("/register")
async def register(data: AuthModel):
    """Registriert einen neuen Benutzer und legt die initialen Spielstrukturen an."""
    existing_user = await User.filter(username=data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Benutzername bereits vergeben")

    user = await User.create(username=data.username, password_hash=data.password)
    player = await PlayerState.create(user=user, gold=100, wood=0)

    return {"status": "success", "player_id": player.id}

@router.post("/login")
async def login(data: AuthModel):
    """Authentifiziert einen Benutzer und gibt die interne Spieler-ID zurück."""
    user = await User.filter(username=data.username).prefetch_related("player_state").first()
    if not user or user.password_hash != data.password:
        raise HTTPException(status_code=400, detail="Ungültige Zugangsdaten")

    return {"status": "success", "player_id": user.player_state.id}
