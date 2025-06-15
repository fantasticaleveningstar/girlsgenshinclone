from enum import Enum, auto
import random
import heapq
import itertools
import uuid
from dataclasses import dataclass, field
from collections import defaultdict
from typing import Optional, Callable
from core import Character, Element, DamageInstance, StatType, Aura, Summon, DamageType
from turn import TurnManager

ELEMENT_EMOJIS = {
    Element.PYRO: "🔥",
    Element.HYDRO: "💧",
    Element.CRYO: "❄️",
    Element.ELECTRO: "⚡",
    Element.GEO: "💎",
    Element.ANEMO: "🌪️",
    Element.DENDRO: "🌿",
    Element.QUANTUM: "🔮",
    Element.IMAGINARY: "✨"
}

REACTION_EMOJIS = {
    "Forward Melt": "💥❄️🔥",
    "Reverse Melt": "❄️💥🔥",
    "Forward Vaporize": "💧🔥💨",
    "Reverse Vaporize": "🔥💧💨",
    "Overload": "💣🔥⚡",
    "Freeze": "❄️❄️💧",
    "Superconduct": "⚡❄️💥",
    "Superposition": "🔗🔮",
    "Burning": "🔥🌿",
    "Bloom": "🌸💧🌿",
}

REACTION_AURA_CONSUMPTION = {
    "Forward Melt": 2.0,
    "Reverse Melt": 1.0,
    "Forward Vaporize": 2.0,
    "Reverse Vaporize": 1.0,
    "Overload": 1.0,
    "Superconduct": 1.0,
    "Burning": 0.5,
    "Bloom": 0.5,
    "Superposition": 2.0,
    "Rimegrass": 1.0,
    # Add more if needed
}

class ReactionHit:
    def __init__(self, source: Character, target: Character, reaction: str, damage: float, element: Element):
        self.source = source
        self.target = target
        self.reaction = reaction
        self.damage = damage
        self.element = element
    
    def resolve(self):
        print(f"{self.reaction} deals {int(self.damage)} damage to {self.target.name}!")

class ICDTracker:
    def __init__(self, tag=None, interval=3):
        self.hit_counter = 0
        self.tag = tag
        self.interval = interval

    def register_hit(self) -> bool:
        if self.hit_counter == 0:
            self.hit_counter = 1
            return True
        else:
            self.hit_counter += 1
            if self.hit_counter >= self.interval:
                self.hit_counter = 0
            return False

def calculate_dmg_bonus(attacker: Character, instance: DamageInstance) -> float:
    base = attacker.general_dmg_bonus
    base += attacker.elemental_bonuses.get(instance.element, 0.0)
    base += attacker.type_bonuses.get(instance.damage_type, 0.0)
    # TODO: conditional bonuses, e.g., vs frozen, HP thresholds, buffs
    return base

def calculate_def_multiplier(attacker: Character, defender: Character, def_shred: float = 0.0):
    atk_level = getattr(attacker, "level", 90)
    def_level = getattr(defender, "level", 90)
    def_multiplier = (atk_level + 100) / ((atk_level + 100) + (def_level + 100) * (1 - def_shred))
    return def_multiplier

def calculate_res_multiplier(defender: Character, element: Element):
    res = defender.resistances.get(element, 0.1)  # Default to 10% res

    if res < 0:
        return 1 - (res / 2)
    elif res < 0.75:
        return 1 - res
    else:
        return 1 / (4 * res + 1)

def calculate_damage(attacker: Character, defender: Character, instance: DamageInstance):
    #Base DMG
    base_stat = attacker.get_stat(instance.scaling_stat)
    base_damage = (base_stat * instance.multiplier * instance.base_dmg_multiplier)

    #Additive Bonuses
    base_damage += instance.additive_base_dmg_bonus

    #Apply DMG Bonuses
    bonus = calculate_dmg_bonus(attacker, instance)
    reduction = defender.dmg_reduction_taken
    multiplier = 1 + bonus - reduction
    base_damage *= multiplier

    # CRIT calculation
    crit_rate = attacker.get_stat(StatType.CRIT_RATE)
    crit_dmg = attacker.get_stat(StatType.CRIT_DMG)
    is_crit = random.random() < crit_rate
    if is_crit:
        base_damage *= (1 + crit_dmg)
    
    #DEF and RES
    def_mult = calculate_def_multiplier(attacker, defender)
    res_mult = calculate_res_multiplier(defender, instance.element)
    base_damage *= def_mult * res_mult

    effective_element = instance.element
    reaction_hits = []

    # === Elemental application logic ===
    if effective_element:
        defender.apply_elemental_effect(
            element=effective_element,
            attacker=attacker,
            icd_tag=instance.icd_tag,
            icd_interval=instance.icd_interval
        )

        # Step 2: Check for a reaction
        reaction, reacted_with = check_reaction(effective_element, defender.auras)
        if reaction:
            emoji = REACTION_EMOJIS.get(reaction, "💥")
            print(f"{emoji} {reaction} triggered by {attacker.name}!")

            # Transformative reactions deal separate damage
            if is_transformative(reaction):
                reaction_damage = round(calculate_transformative_damage(reaction, attacker))
                reaction_hits.append(ReactionHit(
                    source=attacker,
                    target=defender,
                    reaction=reaction,
                    damage=reaction_damage,
                    element=effective_element
                ))

            # Amplifying reactions modify base damage
            elif is_amplifying(reaction):
                reaction_bonus = calculate_amplifying_damage(reaction, attacker)
                base_damage *= reaction_bonus
            # Additive reactions like Aggravate/Spread
            elif reaction == "Aggravate":
                base_damage += check_aggravate(attacker, defender, effective_element)
            elif reaction == "Spread":
                base_damage += check_spread(attacker, defender, effective_element)
           # Handle aura consumption
            if is_consuming_reaction(reaction) and reacted_with in defender.auras:
                if isinstance(reacted_with, Aura):
                    consume_aura_units(defender, reacted_with.element, reaction=reaction)

    # Final damage logging
    total_damage = round(base_damage)
    element_icon = ELEMENT_EMOJIS.get(effective_element, "")
    print(f"{'CRIT! ' if is_crit else ''}{attacker.name} dealt {total_damage} {element_icon} damage to {defender.name}.")
    
    return total_damage, reaction_hits

def is_consuming_reaction(reaction: str) -> bool:
    return reaction not in ("Quicken", "Aggravate", "Spread", "Frozen", "Electro-Charged", "Burning")

def check_aggravate(attacker: Character, defender: Character, damage_element: Element):
    if damage_element != Element.ELECTRO:
        print("[DEBUG] Aggravate not triggered. Not Electro attack.")
        return 0
    if not any(a.name == "Quicken" for a in defender.auras):
        print("[DEBUG] Aggravate not triggered. No Quicken aura.")
        return 0
    em = attacker.stats.get(StatType.EM, 0)
    bonus_damage = 1.15 * 1447 * (1 + (5 * em / (em + 1200)))
    print(f"[DEBUG] Aggravate triggered. EM: {em}, Bonus: {bonus_damage}")
    return bonus_damage

def check_spread(attacker: Character, defender: Character, damage_element: Element):
    if damage_element == Element.DENDRO and any(a.name == "Quicken" for a in defender.auras):
        em = attacker.stats.get(StatType.EM, 0)
        bonus_damage = 1.25 * 1447 * (1 + (5 * em / (em + 1200)))
        return bonus_damage
    return 0

def get_amplifying_multiplier(reaction: str) -> float:
    return {
        "Forward Vaporize": 2.0,
        "Reverse Vaporize": 1.5,
        "Forward Melt": 2.0,
        "Reverse Melt": 1.5,
        "Superposition": 2.25,
    }.get(reaction, 1.0)
    
def calculate_amplifying_damage(reaction: str, attacker: Character) -> float:
    em = attacker.get_stat(StatType.EM)
    base_multi = get_amplifying_multiplier(reaction)
    if reaction == "Superposition":
        em_multi = 1.28
    else:
        em_multi = 2.78
    return base_multi * (1 + (em_multi * (em)/(1400 + em)))

def calculate_transformative_damage(reaction: str, attacker: Character) -> float:
    em = attacker.get_stat(StatType.EM)

    base_damage = 1446  # placeholder value for reaction base damage

    em_bonus = 1 + (16 * em / (em + 2000))
    return base_damage * em_bonus * get_transformative_multiplier(reaction)

def get_transformative_multiplier(reaction: str) -> float:
    return {
        "Burgeon": 3,
        "Hyperbloom": 3,
        "Shatter": 3,
        "Overloaded": 2.75,
        "Electro-Charged": 2,
        "Superconduct": 1.5,
        "Swirl": 0.6,
        "Burning": 0.6,
    }.get(reaction, 1.0)

def is_transformative(reaction: str) -> bool:
    return reaction in {
        "Overload", "Electro-Charged", "Superconduct",
        "Swirl", "Bloom", "Hyperbloom", "Burgeon", "Burning"
        }

def is_amplifying(reaction: str) -> bool:
    return reaction in {
        "Forward Melt", "Forward Vaporize", "Reverse Melt", "Reverse Vaporize", "Superposition", 
        }

def check_reaction(new_element: Element, existing_auras: list):

    reaction_table = {
        (Element.PYRO, Element.HYDRO): "Reverse Vaporize",
        (Element.HYDRO, Element.PYRO): "Forward Vaporize",
        (Element.PYRO, Element.CRYO): "Forward Melt",
        (Element.CRYO, Element.PYRO): "Reverse Melt",
        (Element.ELECTRO, Element.PYRO): "Overload",
        (Element.CRYO, Element.HYDRO): "Freeze",
        (Element.ELECTRO, Element.HYDRO): "Electro-Charged",
        (Element.PYRO, Element.DENDRO): "Burning",
        (Element.CRYO, Element.DENDRO): "Rimegrass",
        (Element.DENDRO, Element.HYDRO): "Bloom",
        (Element.ELECTRO, Element.CRYO): "Superconduct",
        (Element.ELECTRO, Element.DENDRO): "Quicken",
        (Element.DENDRO, Element.ELECTRO): "Quicken",
        # ... add others
    }
    
    if new_element == Element.QUANTUM:
        if len(existing_auras) >= 2:
            return "Superposition", (existing_auras[0], existing_auras[1])
        return None, None


    if any(aura.name == "Quicken" for aura in existing_auras):
        if new_element == Element.ELECTRO:
            print(f"Reaction Aggravate detected with existing Quicken and {new_element.name}")
            return "Aggravate", "Quicken"
        elif new_element == Element.DENDRO:
            print(f"Reaction Spread detected with existing Quicken and {new_element.name}")
            return "Spread", "Quicken"

    
    for aura in existing_auras:
        reaction = reaction_table.get((new_element, aura.element)) or reaction_table.get((aura.element, new_element))
        if reaction:
            print(f"Reaction {reaction} detected between {new_element.name} and {aura.element.name}")
            return reaction, aura
    return None, None

def reaction_effect(reaction: str, attacker: Character, defender: Character):
    if is_transformative(reaction):
        return calculate_transformative_damage(reaction, attacker)
    else:
        return calculate_amplifying_damage(reaction, attacker)

def consume_aura_units(defender: Character, element: Element, reaction: str = None):
    units_to_consume = REACTION_AURA_CONSUMPTION.get(reaction, 1.0)

    for aura in defender.auras:
        if aura.element == element and not aura.locked:
            aura.units = max(0, aura.units - units_to_consume)
            if aura.units <= 0:
                print(f"{element.name} aura on {defender.name} fully consumed.")
                defender.auras.remove(aura)
            else:
                print(f"{units_to_consume}U of {element.name} aura consumed. Remaining: {aura.units:.2f}U")
            break

def apply_icd(attacker: Character, defender: Character, instance: DamageInstance) -> bool:
    if not instance.icd_tag:
        return True

    key = (defender, instance.icd_tag)
    tracker = attacker.icd_trackers.get(key)

    if tracker is None:
        tracker = ICDTracker(tag=instance.icd_tag, interval=instance.icd_interval)
        attacker.icd_trackers[key] = tracker

    if tracker.register_hit():
        return True
    else:
        return False

#character-specific
def salon_attack_action(summon: 'Summon', enemy_team: list[Character]):
    if not enemy_team:
        return

    target = random.choice(enemy_team)
    owner = summon.owner
    drained_allies = 0
    damage_multiplier = summon.stats.get("multiplier", 0.1)
    base_drain = summon.stats.get("hp_drain", 0.08)
    max_scaling = summon.stats.get("scaling_cap", 1.5)

    for ally in summon.owner_team:
        min_allowed = ally.max_hp * 0.5
        if ally.current_hp > min_allowed:
            drain_amount = min(ally.current_hp - min_allowed, ally.max_hp * base_drain)
            ally.current_hp -= drain_amount
            drained_allies += 1
            print(f"{summon.name} drains {drain_amount:.0f} HP from {ally.name}.")

    total_multiplier = damage_multiplier * (1 + 0.25 * drained_allies)
    total_multiplier = min(total_multiplier, damage_multiplier * max_scaling)

    damage_instance = DamageInstance(
        multiplier=total_multiplier,
        scaling_stat=StatType.HP,
        damage_type=DamageType.SKILL,
        element=Element.HYDRO,
        description=f"{summon.name}'s Hydro Strike",
        icd_tag=f"{summon.name}_Strike"
    )

    damage, reactions = calculate_damage(owner, target, damage_instance)
    print(f"{summon.name} strikes {target.name} for {damage} Hydro damage.")
    target.current_hp = max(target.current_hp - damage, 0)

    for r in reactions:
        r.resolve()
        r.target.current_hp = max(r.target.current_hp - r.damage, 0)
        print(f"{r.target.name}'s HP after reaction: {r.target.current_hp}/{r.target.max_hp}")

def summon_salon_members(attacker: Character, defender: Character, turn_manager: TurnManager):
    attacker.summon_turn_counter = 3  # custom duration

    salon_summons = [
        ("Gentilhomme Usher", 0.08, 110, 0.05),
        ("Surintendante Chevalmarin", 0.12, 90, 0.07),
        ("Mademoiselle Crabaletta", 0.15, 100, 0.1),
    ]

    for name, multiplier, speed, hp_drain in salon_summons:
        summon = Summon(
            name=name,
            owner=attacker,
            stats={"multiplier": multiplier, "hp_drain": hp_drain, "scaling_cap": 2.0},
            hp=1,
            duration=None,  # We’ll expire manually
            speed=speed,
            is_stationary=False,
            triggers={
                "on_action": lambda self, enemy_team: salon_attack_action(self, enemy_team)
            }
        )
        summon.owner_team = [attacker]  # or attacker + allies if using full team ref
        attacker.summons.append(summon)
        turn_manager.add_summon(summon)
        print(f"{attacker.name} summons {name}.")

    return 0, []
