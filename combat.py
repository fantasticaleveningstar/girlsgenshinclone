from enum import Enum, auto
import random
import heapq
import itertools
import uuid
from dataclasses import dataclass, field
from collections import defaultdict
from typing import Optional, Callable
from core import Character, Element, DamageInstance, StatType, Aura, Summon, DamageType, AuraTag
from turn import TurnManager, Buff
from constants import ELEMENT_EMOJIS
from dendro_core import spawn_dendro_core
from combat_helpers import *
from event_system import *

def get_targets_in_radius(center: Character, candidates: list[Character], radius: float) -> list[Character]:
    return [unit for unit in candidates if unit != center and distance(center, unit) <= radius]

def heal(target: Character, amount: int, source: Optional[Character] = None, team: Optional[list[Character]] = None):
    if team is None:
        team = [target]  # fallback if team not passed

    old_hp = target.current_hp
    max_heal = target.max_hp - target.current_hp
    actual_heal = min(amount, max_heal)
    target.current_hp += actual_heal

    log_heal(source or target, target, actual_heal)
    notify_hp_change(target, old_hp, target.current_hp, team)

    return actual_heal

def take_damage(target: Character, amount: int, source: Optional[Character] = None, team: Optional[list[Character]] = None, summary: Optional[dict] = None, taken_summary: Optional[dict] = None):
    if team is None:
        team = [target]  # fallback if team not passed

    old_hp = target.current_hp
    target.current_hp = max(0, target.current_hp - amount)

    # Update damage dealt tracker
    if source and summary is not None:
        summary[source.name] += amount
    if taken_summary is not None:
        taken_summary[target.name] += amount

    notify_hp_change(target, old_hp, target.current_hp, team)

    return amount

def apply_damage_instance(attacker: Character, instance: DamageInstance, targets: list[Character], turn_manager):
    for target in targets:
        calculate_damage(attacker, target, instance, turn_manager)

def resolve_reactions(reactions: list, team: list[Character]):
    for r in reactions:
        r.resolve()
        actual = take_damage(r.target, r.damage, source=r.source, team=team)
        log_damage(
            source=r.source,
            target=r.target,
            amount=actual,
            element=r.element,
            crit=False,
            label=r.reaction,
            is_reaction=True,
            applied_element=True
        )

#character-specific

#Furina
def salon_attack_action(summon: 'Summon', enemy_team: list[Character]):
    if not enemy_team:
        return

    target = random.choice(enemy_team)
    owner = summon.owner
    drained_allies = 0
    damage_multiplier = summon.stats.get("multiplier", 0.1)
    base_drain = summon.stats.get("hp_drain", 0.016)
    max_scaling = summon.stats.get("scaling_cap", 1.4)

    # Drain allies' HP
    for ally in summon.owner_team:
        min_allowed = ally.max_hp * 0.5
        if ally.current_hp > min_allowed:
            drain_amount = min(ally.current_hp - min_allowed, ally.max_hp * base_drain)
            ally.current_hp -= drain_amount
            notify_hp_change(ally, old_hp=ally.current_hp + drain_amount, new_hp=ally.current_hp, team=summon.owner_team)
            drained_allies += 1
            print(f"{summon.name} drains {drain_amount:.0f} HP from {ally.name}.")

    total_multiplier = damage_multiplier * (1 + 0.1 * drained_allies)
    total_multiplier = min(total_multiplier, damage_multiplier * max_scaling)

    damage_instance = DamageInstance(
        multiplier=total_multiplier,
        scaling_stat=StatType.HP,
        damage_type=DamageType.SKILL,
        element=Element.HYDRO,
        description=f"{summon.name}'s Hydro Strike",
        icd_tag=f"{summon.name}_Strike"
    )

    # Correctly unpack from dict
    result = calculate_damage(owner, target, damage_instance)
    damage = result["damage"]
    reactions = result["reactions"]

    # Apply damage properly
    actual = take_damage(target, damage, source=owner, team=[target])
    log_damage(
        source=owner,
        target=target,
        amount=actual,
        element=result["element"],
        crit=result["crit"],
        label=result["label"],
        is_reaction=False,
        applied_element=result.get("applied_element", False)
    )

    # Apply reaction damage (if any)
    for r in reactions:
        r.resolve()
        actual_reaction = take_damage(r.target, r.damage, source=r.source, team=[r.target])
        log_damage(
            source=r.source,
            target=r.target,
            amount=actual_reaction,
            element=r.element,
            crit=False,
            label=r.reaction,
            is_reaction=True,
            applied_element=True
        )

def summon_salon_members(attacker: Character, defender: Character, turn_manager: TurnManager, **kwargs):
    attacker.summon_turn_counter = 3

    team1, team2 = get_teams(turn_manager)
    allies = team1 if attacker in team1 else team2

    salon_summons = [
        ("Gentilhomme Usher", 0.1013, 110, 0.024),
        ("Surintendante Chevalmarin", 0.0549, 130, 0.016),
        ("Mademoiselle Crabaletta", 0.1409, 90, 0.036),
    ]

    for name, multiplier, speed, hp_drain in salon_summons:
        summon = Summon(
            name=name,
            owner=attacker,
            stats={"multiplier": multiplier, "hp_drain": hp_drain, "scaling_cap": 1.4},
            hp=1,
            duration=None,  # We’ll expire manually
            speed=speed,
            is_stationary=False,
            triggers={
                "on_action": lambda self, enemy_team: salon_attack_action(self, enemy_team)
            }
        )
        summon.owner_team = allies
        attacker.summons.append(summon)
        turn_manager.add_summon(summon)
        print(f"{attacker.name} summons {name}.")

    return 0, []
