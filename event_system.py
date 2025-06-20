from core import Character
from typing import Optional

def trigger_event(event_name: str, team: list[Character], **kwargs):
    for unit in team:
        # Passives
        for passive in getattr(unit, "passives", []):
            if passive.trigger == event_name:
                kwargs["observer"] = unit
                passive.effect(**kwargs)

        # Buffs
        for buff in getattr(unit, "buffs", []):
            if buff.trigger == event_name and buff.effect:
                if "unit" not in kwargs:
                    buff.effect(unit=unit, buff=buff, **kwargs)
                else:
                    buff.effect(buff=buff, **kwargs)

def trigger_event_for_unit(event_name: str, unit: Character, **kwargs):
    for passive in getattr(unit, "passives", []):
        if passive.trigger == event_name:
            passive.effect(observer=unit, **kwargs)

def notify_hp_change(unit: Character, old_hp: int, new_hp: int, team: list[Character]):
    diff = abs(new_hp - old_hp)
    if diff > 0:
        trigger_event("on_hp_change", team, unit=unit, old_hp=old_hp, new_hp=new_hp)

def notify_damage_taken(target: Character, amount: int, source: Optional[Character], team: list[Character]):
    trigger_event("on_damage_taken", team, target=target, amount=amount, source=source)
