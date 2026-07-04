from dataclasses import dataclass


@dataclass(frozen=True)
class WeaponSeed:
    id: str
    name: str
    required_role: str
    price: int
    attack_bonus: int
    description: str


WEAPONS: list[WeaponSeed] = [
    WeaponSeed(
        id="wooden_tanto",
        name="Wooden Tanto",
        required_role="Hero",
        price=0,
        attack_bonus=0,
        description="Starter practice blade.",
    ),
    WeaponSeed(
        id="iron_katana",
        name="Iron Katana",
        required_role="Hero",
        price=80,
        attack_bonus=8,
        description="Reliable blade for longer battle runs.",
    ),
    WeaponSeed(
        id="oni_slayer",
        name="Oni Slayer",
        required_role="Hero",
        price=220,
        attack_bonus=18,
        description="Heavy weapon tuned for hard and extreme stages.",
    ),
]
