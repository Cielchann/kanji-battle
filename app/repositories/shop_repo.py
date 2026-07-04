from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.data.weapons import WEAPONS
from app.db.models import PlayerProfileRecord, PlayerWeaponRecord, WeaponRecord
from app.schemas.shop import Weapon, WeaponActionResult


def _weapon_schema(
    weapon: WeaponRecord,
    owned: bool = False,
    equipped: bool = False,
) -> Weapon:
    return Weapon(
        id=weapon.id,
        name=weapon.name,
        required_role=weapon.required_role,
        price=weapon.price,
        attack_bonus=weapon.attack_bonus,
        description=weapon.description,
        owned=owned,
        equipped=equipped,
    )


class ShopRepository:
    def seed_weapons(self, db: Session) -> None:
        existing = {
            weapon.id: weapon
            for weapon in db.scalars(select(WeaponRecord)).all()
        }
        for seed in WEAPONS:
            weapon = existing.get(seed.id)
            if weapon is None:
                db.add(
                    WeaponRecord(
                        id=seed.id,
                        name=seed.name,
                        required_role=seed.required_role,
                        price=seed.price,
                        attack_bonus=seed.attack_bonus,
                        description=seed.description,
                    )
                )
                continue
            weapon.name = seed.name
            weapon.required_role = seed.required_role
            weapon.price = seed.price
            weapon.attack_bonus = seed.attack_bonus
            weapon.description = seed.description
        db.commit()

    def grant_starter_weapon(self, db: Session, player_name: str) -> None:
        existing = db.scalar(
            select(PlayerWeaponRecord).where(
                PlayerWeaponRecord.player_name == player_name,
                PlayerWeaponRecord.weapon_id == "wooden_tanto",
            )
        )
        if existing is not None:
            return
        db.add(
            PlayerWeaponRecord(
                player_name=player_name,
                weapon_id="wooden_tanto",
                is_equipped=self.get_equipped_weapon(db, player_name) is None,
            )
        )
        db.commit()

    def list_weapons(self, db: Session, player_name: str) -> list[Weapon]:
        self.grant_starter_weapon(db, player_name)
        owned_records = db.scalars(
            select(PlayerWeaponRecord).where(PlayerWeaponRecord.player_name == player_name)
        ).all()
        owned_by_id = {record.weapon_id: record for record in owned_records}

        weapons = db.scalars(select(WeaponRecord).order_by(WeaponRecord.price)).all()
        return [
            _weapon_schema(
                weapon,
                owned=weapon.id in owned_by_id,
                equipped=owned_by_id.get(weapon.id).is_equipped
                if weapon.id in owned_by_id
                else False,
            )
            for weapon in weapons
        ]

    def buy_weapon(self, db: Session, player_name: str, weapon_id: str) -> WeaponActionResult:
        self.grant_starter_weapon(db, player_name)
        profile = db.get(PlayerProfileRecord, player_name)
        if profile is None:
            profile = PlayerProfileRecord(
                player_name=player_name,
                hero_role="Hero",
                xp=0,
                gold=0,
                total_clears=0,
            )
            db.add(profile)
            db.commit()

        weapon = db.get(WeaponRecord, weapon_id)
        if weapon is None:
            raise ValueError("Weapon not found.")

        existing = db.scalar(
            select(PlayerWeaponRecord).where(
                PlayerWeaponRecord.player_name == player_name,
                PlayerWeaponRecord.weapon_id == weapon_id,
            )
        )
        if existing is not None:
            return WeaponActionResult(
                player_name=player_name,
                weapon=_weapon_schema(weapon, owned=True, equipped=existing.is_equipped),
                gold=profile.gold,
            )

        if profile.gold < weapon.price:
            raise ValueError("Not enough gold.")

        profile.gold -= weapon.price
        player_weapon = PlayerWeaponRecord(
            player_name=player_name,
            weapon_id=weapon_id,
            is_equipped=False,
        )
        db.add(player_weapon)
        db.commit()

        return WeaponActionResult(
            player_name=player_name,
            weapon=_weapon_schema(weapon, owned=True, equipped=False),
            gold=profile.gold,
        )

    def equip_weapon(self, db: Session, player_name: str, weapon_id: str) -> WeaponActionResult:
        self.grant_starter_weapon(db, player_name)
        player_weapon = db.scalar(
            select(PlayerWeaponRecord).where(
                PlayerWeaponRecord.player_name == player_name,
                PlayerWeaponRecord.weapon_id == weapon_id,
            )
        )
        if player_weapon is None:
            raise ValueError("Weapon is not owned.")

        db.execute(
            update(PlayerWeaponRecord)
            .where(PlayerWeaponRecord.player_name == player_name)
            .values(is_equipped=False)
        )
        player_weapon.is_equipped = True
        db.commit()

        weapon = db.get(WeaponRecord, weapon_id)
        profile = db.get(PlayerProfileRecord, player_name)
        return WeaponActionResult(
            player_name=player_name,
            weapon=_weapon_schema(weapon, owned=True, equipped=True),
            gold=profile.gold if profile is not None else 0,
        )

    def get_equipped_weapon(self, db: Session, player_name: str) -> WeaponRecord | None:
        record = db.scalar(
            select(PlayerWeaponRecord).where(
                PlayerWeaponRecord.player_name == player_name,
                PlayerWeaponRecord.is_equipped.is_(True),
            )
        )
        if record is None:
            return None
        return db.get(WeaponRecord, record.weapon_id)
