# dendro_core.py

from dataclasses import dataclass
from typing import TYPE_CHECKING
from core import Element, distance

if TYPE_CHECKING:
    from core import Character, TurnManager, Position

@dataclass
class DendroCore:
    creator: 'Character'
    position: 'Position'
    turns_remaining: int = 3
    active: bool = True

def spawn_dendro_core(creator: 'Character', target: 'Character', turn_manager: 'TurnManager'):
    core = DendroCore(creator=creator, position=target.position)
    turn_manager.field_objects.append(core)
    print(f"🌱 Dendro Core created at {core.position} by {creator.name}")

def trigger_hyperbloom(core: DendroCore, attacker: 'Character', turn_manager: 'TurnManager'):
    from combat import calculate_transformative_damage, take_damage, log_damage, get_enemies
    enemies = get_enemies(attacker, turn_manager)
    if not enemies:
        return

    target = min(enemies, key=lambda u: distance(u, core.position))
    dmg = calculate_transformative_damage("Hyperbloom", attacker)["damage"]

    print(f"⚡ Hyperbloom from {core.creator.name} hits {target.name}!")
    take_damage(target, dmg, source=attacker, team=[target])
    log_damage(attacker, target, dmg, Element.DENDRO, crit=False, label="Hyperbloom")

    core.active = False

def trigger_burgeon(core: DendroCore, attacker: 'Character', turn_manager: 'TurnManager'):
    from combat import calculate_transformative_damage, take_damage, log_damage, get_enemies, get_targets_in_radius
    enemies = get_enemies(attacker, turn_manager)
    targets = get_targets_in_radius(core, enemies, radius=2.0)
    dmg = calculate_transformative_damage("Burgeon", attacker)["damage"]

    print(f"🔥 Burgeon erupts from Dendro Core at {core.position}!")
    for target in targets:
        take_damage(target, dmg, source=attacker, team=[target])
        log_damage(attacker, target, dmg, Element.DENDRO, crit=False, label="Burgeon")

    core.active = False

def update_dendro_cores(turn_manager: 'TurnManager'):
    for core in turn_manager.field_objects:
        if isinstance(core, DendroCore):
            core.turns_remaining -= 1
            if core.turns_remaining <= 0:
                core.active = False
    turn_manager.field_objects = [c for c in turn_manager.field_objects if getattr(c, "active", True)]
