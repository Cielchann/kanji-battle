from pydantic import BaseModel, Field


class Weapon(BaseModel):
    id: str
    name: str
    required_role: str
    price: int = Field(ge=0)
    attack_bonus: int = Field(ge=0)
    description: str
    owned: bool = False
    equipped: bool = False


class BuyWeaponRequest(BaseModel):
    player_name: str = Field(min_length=1, max_length=40)
    device_token: str = Field(min_length=16, max_length=128)
    weapon_id: str


class EquipWeaponRequest(BaseModel):
    player_name: str = Field(min_length=1, max_length=40)
    device_token: str = Field(min_length=16, max_length=128)
    weapon_id: str


class WeaponActionResult(BaseModel):
    player_name: str
    weapon: Weapon
    gold: int = Field(ge=0)
