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
    "Reverse Melt": 0.5,
    "Forward Vaporize": 2.0,
    "Reverse Vaporize": 0.5,
    "Overload": 1.0,
    "Superconduct": 1.0,
    "Burning": 0.5,
    "Bloom": 0.5,
    "Superposition": 2.0,
    "Rimegrass": 1.0,
    "Stasis": 1.0,
    # Add more if needed
}

class TextColor:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    GRAY = "\033[90m"
    WHITE = "\033[97m"
    HEAL = "\033[38;2;149;224;33m"

ELEMENT_COLORS = {
    Element.PYRO: "\033[38;2;255;102;64m",
    Element.HYDRO: "\033[38;2;0;192;255m",
    Element.ELECTRO: "\033[38;2;204;128;255m",
    Element.CRYO: "\033[38;2;122;242;242m",
    Element.GEO: "\033[38;2;255;176;13m",
    Element.ANEMO: "\033[38;2;51;215;160m",
    Element.DENDRO: "\033[38;2;155;229;61m",
    Element.QUANTUM: "\033[38;2;111;102;221m",
    Element.IMAGINARY: "\033[38;2;212;189;77m",
    Element.PHYSICAL: "\033[97m",  # fallback bright white
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

def notify_hp_change(unit: Character, old_hp: int, new_hp: int, team: list[Character]):
    diff = abs(new_hp - old_hp)
    if diff > 0:
        trigger_event("on_hp_change", team, unit=unit, old_hp=old_hp, new_hp=new_hp)

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

def calculate_dmg_bonus(attacker: Character, instance: DamageInstance) -> float:
    bonus = 0.0

    bonus += attacker.general_dmg_bonus
    bonus += attacker.elemental_bonuses.get(instance.element, 0.0)
    bonus += attacker.type_bonuses.get(instance.damage_type, 0.0)
    # TODO: conditional bonuses, e.g., vs frozen, HP thresholds, buffs
    return bonus

def calculate_def_multiplier(attacker: Character, defender: Character, def_shred: float = 0.0):
    atk_level = getattr(attacker, "level", 90)
    def_level = getattr(defender, "level", 90)
    def_multiplier = (atk_level + 100) / ((atk_level + 100) + (def_level + 100) * (1 - def_shred))
    return def_multiplier

def calculate_res_multiplier(defender: Character, element: Element) -> float:
    res = defender.resistances[element]  # Default to 10% res

    if res < 0:
        return 1 - (res / 2)
    elif res < 0.75:
        return 1 - res
    else:
        return 1 / (4 * res + 1)

def calculate_damage(attacker: Character, defender: Character, instance: DamageInstance, turn_manager: TurnManager):
    base_stat = attacker.get_stat(instance.scaling_stat)
    base_damage = (base_stat * instance.multiplier * instance.base_dmg_multiplier)
    base_damage += instance.additive_base_dmg_bonus

    bonus = calculate_dmg_bonus(attacker, instance)
    reduction = defender.dmg_reduction_taken
    multiplier = 1 + bonus - reduction
    base_damage *= multiplier

    crit_rate = attacker.get_stat(StatType.CRIT_RATE)
    crit_dmg = attacker.get_stat(StatType.CRIT_DMG)
    is_crit = random.random() < crit_rate
    if is_crit:
        base_damage *= (1 + crit_dmg)

    def_mult = calculate_def_multiplier(attacker, defender)
    res_mult = calculate_res_multiplier(defender, instance.element)
    base_damage *= def_mult * res_mult

    effective_element = instance.element
    reaction_hits = []
    applied_element = False
    reaction_name = None
    reacted_with_aura = None

    if effective_element:
        # Track new elements
        if not hasattr(defender, "_just_applied_elements"):
            defender._just_applied_elements = set()
        defender._just_applied_elements.add(effective_element)

        reaction_info = check_reaction(
            new_element=effective_element,
            existing_auras=defender.auras[:],
            just_applied_elements=defender._just_applied_elements
        )

        defender.apply_elemental_effect(
            element=effective_element,
            attacker=attacker,
            units=1.0
        )
        applied_element = True

        if reaction_info:
            if isinstance(reaction_info, tuple):
                reaction_name, reacted_with_aura = reaction_info
            else:
                reaction_name = reaction_info.get("reaction")
                reacted_with_aura = reaction_info.get("triggering_aura")

            # Resolve the reaction normally
            reaction_result_data = resolve_reaction_effect(reaction_name, attacker, defender, turn_manager)
            reaction_hits.extend(reaction_result_data)

            emoji = REACTION_EMOJIS.get(reaction_name, "💥")
            print(f"{emoji} {reaction_name} triggered by {attacker.name}!")

            # Handle reaction-based damage bonuses or special logic
            reaction_hit_exists = any(isinstance(r, ReactionHit) and is_transformative(r.reaction) for r in reaction_result_data)
            if is_transformative(reaction_name) and not reaction_hit_exists:
                reaction_result = calculate_transformative_damage(reaction_name, attacker)
                reaction_hits.append(ReactionHit(
                    source=attacker,
                    target=defender,
                    reaction=reaction_result["label"],
                    damage=reaction_result["damage"],
                    element=reaction_result["element"]
                ))

            elif is_amplifying(reaction_name):
                reaction_bonus = calculate_amplifying_damage(reaction_name, attacker)
                base_damage *= reaction_bonus

            elif reaction_name == "Aggravate":
                base_damage += check_aggravate(attacker, defender, effective_element)

            elif reaction_name == "Spread":
                base_damage += check_spread(attacker, defender, effective_element)

            # Consume aura units if appropriate
            if reacted_with_aura and is_consuming_reaction(reaction_name):
                consume_aura_units(defender, reacted_with_aura.element, reaction=reaction_name)


    if hasattr(defender, "_just_applied_elements"):
        del defender._just_applied_elements

    total_damage = round(base_damage)

    return {
        "damage": total_damage,
        "crit": is_crit,
        "element": effective_element,
        "label": instance.description or "",
        "reactions": reaction_hits,
        "applied_element": applied_element
    }

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
    final_damage = base_damage * em_bonus * get_transformative_multiplier(reaction)

    if reaction in ["Bloom", "Hyperbloom", "Burgeon"]:
        element = Element.DENDRO
    elif reaction == "Overloaded":
        element = Element.PYRO
    elif reaction == "Electro-Charged":
        element = Element.ELECTRO
    elif reaction == "Superconduct":
        element = Element.CRYO
    elif reaction == "Swirl":
        element = Element.ANEMO
    elif reaction == "Shatter":
        element = Element.PHYSICAL
    elif reaction == "Stasis":
        element = Element.IMAGINARY
    elif reaction == "Ignition":
        element = Element.IMAGINARY
    elif reaction == "Impulse":
        element = Element.IMAGINARY
    elif reaction == "Anchor":
        element = Element.IMAGINARY
    else:
        element = Element.PHYSICAL  # fallback

    return {
        "damage": int(final_damage),
        "element": element,
        "label": reaction,
        "crit": False
    }

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
        "Stasis": 2.25,
        "Ignition": 2.25,
        "Impulse": 2.25,
        "Anchor": 2.25,
    }.get(reaction, 1.0)

def is_transformative(reaction: str) -> bool:
    return reaction in {
        "Overload", "Electro-Charged", "Superconduct",
        "Swirl", "Bloom", "Hyperbloom", "Burgeon", "Burning", "Stasis", "Ignition", "Impulse", "Anchor"
        }

def is_amplifying(reaction: str) -> bool:
    return reaction in {
        "Forward Melt", "Forward Vaporize", "Reverse Melt", "Reverse Vaporize", "Superposition", 
        }

def check_reaction(new_element: Element, existing_auras: list, just_applied_elements: Optional[set] = None):
    if just_applied_elements is None:
        just_applied_elements = set()

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
        (Element.CRYO, Element.IMAGINARY): "Stasis",
        (Element.PYRO, Element.IMAGINARY): "Ignition",
        (Element.HYDRO, Element.IMAGINARY): "Anchor",
        (Element.ELECTRO, Element.IMAGINARY): "Impulse",
    }
    
    if new_element == Element.QUANTUM:
        for aura in existing_auras:
            if any(tag in aura.tags for tag in AuraTag):
                return "Superposition", aura


    if any(aura.name == "Quicken" for aura in existing_auras):
        if new_element == Element.ELECTRO:
            print(f"Reaction Aggravate detected with existing Quicken and {new_element.name}")
            return "Aggravate", "Quicken"
        elif new_element == Element.DENDRO:
            print(f"Reaction Spread detected with existing Quicken and {new_element.name}")
            return "Spread", "Quicken"

    for aura in existing_auras:
        source_elements = aura.source_elements or {aura.element}
        for elem in source_elements:
            reaction = reaction_table.get((new_element, elem)) or reaction_table.get((elem, new_element))
            if reaction:
                print(f"Reaction {reaction} detected between {new_element.name} and {elem.name}")
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
        print(f"[DEBUG] {element.name} aura on {defender.name} has {aura.units:.2f}U before consumption")
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

def notify_damage_taken(target: Character, amount: int, source: Optional[Character], team: list[Character]):
    trigger_event("on_damage_taken", team, target=target, amount=amount, source=source)

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

def resolve_reaction_effect(reaction: str, attacker: Character, defender: Character, turn_manager: TurnManager) -> list[ReactionHit]:
    hits = []
    def apply_superconduct(unit, **kwargs):
        unit.resistances[Element.PHYSICAL] -= 0.4

    def remove_superconduct(unit):
        unit.resistances[Element.PHYSICAL] += 0.4

    if reaction == "Superconduct":
        debuff = Buff(
            name="Superconduct",
            description="-40% Physical RES",
            duration=2,
            reversible=True,
            effect=apply_superconduct,
            cleanup_effect=remove_superconduct,
        )
        defender.buffs.append(debuff)
        print(f"🧊⚡ {defender.name} is affected by Superconduct (−40% Physical RES)!")

    elif reaction == "Rimegrass":
        aura = Aura(element=Element.CRYO, name="Frost-Twined", units=5)
        defender.auras.append(aura)
        print(f"🌿❄️ {defender.name} is now Frost-Twined (x5 Cryo/Dendro multiplier)!")

    elif reaction == "Stasis":
            print(f"🌀 {defender.name} is afflicted by Stasis — delaying turn!")
            turn_manager.delay_by_percent(defender, 0.25)  # Apply the AV delay

            damage = calculate_transformative_damage("Stasis", attacker)
            hits.append(ReactionHit(
                source=attacker,
                target=defender,
                reaction=damage["label"],
                damage=damage["damage"],
                element=damage["element"]
            ))
    elif reaction == "Ignition":
            print(f"🌀 {defender.name} is afflicted by Ignition — increasing speed!")
            turn_manager.delay_by_percent(defender, -0.6)  # Apply the SPD increase

            damage = calculate_transformative_damage("Ignition", attacker)
            hits.append(ReactionHit(
                source=attacker,
                target=defender,
                reaction=damage["label"],
                damage=damage["damage"],
                element=damage["element"]
            ))
    elif reaction == "Impulse":
            print(f"🌀 {defender.name} is afflicted by Impulse — advancing action!")
            turn_manager.delay_by_percent(defender, -0.25)  # Apply the AV advance

            damage = calculate_transformative_damage("Impulse", attacker)
            hits.append(ReactionHit(
                source=attacker,
                target=defender,
                reaction=damage["label"],
                damage=damage["damage"],
                element=damage["element"]
            ))
    elif reaction == "Anchor":
            print(f"🌀 {defender.name} is afflicted by Anchor — decreasing speed!")
            turn_manager.delay_by_percent(defender, 0.6)  # Apply the SPD decrease

            damage = calculate_transformative_damage("Anchor", attacker)
            hits.append(ReactionHit(
                source=attacker,
                target=defender,
                reaction=damage["label"],
                damage=damage["damage"],
                element=damage["element"]
            ))
        
    return hits

def log_damage(source: Character, target: Character, amount: int,
               element: Optional[Element] = None,
               crit: bool = False,
               label: str = "",
               is_reaction: bool = False,
               applied_element: bool = False):

    start = target.current_hp + amount
    end = target.current_hp

    # Format components
    emoji = ELEMENT_EMOJIS.get(element, "") if applied_element and element else ""
    color = ELEMENT_COLORS.get(element, TextColor.WHITE)
    bold = TextColor.BOLD if crit else ""
    reset = TextColor.RESET
    gray = TextColor.GRAY

    # Tags
    tag = "REACTION" if is_reaction else "CRIT" if crit else "DMG"

    # Text segments
    source_str = f"{source.name}'s " if source else ""
    label_str = label or "Hit"
    element_str = f"{element.name.upper()} " if element else ""
    dmg_str = f"{color}{bold}{amount:,}{reset}"

    print(f"{emoji} [{tag}] {source_str}{label_str} hits {target.name} "
          f"for {dmg_str} {element_str}DMG "
          f"{gray}(HP: {start:,} → {end:,}){reset}")

def log_heal(source: Character, target: Character, amount: int):
    start = target.current_hp - amount
    end = target.current_hp
    print(f"[HEAL] 🩹 {source.name} heals {target.name} for {TextColor.HEAL}{amount:,}{TextColor.RESET} HP "
          f"{TextColor.GRAY}(HP: {start:,} → {end:,}){TextColor.RESET}")

def get_allies(attacker: Character, turn_manager: TurnManager) -> list[Character]:
    return [
        unit for unit in turn_manager.units
        if isinstance(unit, Character)
        and is_same_team(attacker, unit, turn_manager)
    ]

def get_enemies(attacker: Character, turn_manager: TurnManager) -> list[Character]:
    return [
        unit for unit in turn_manager.units
        if isinstance(unit, Character)
        and not is_same_team(attacker, unit, turn_manager)
    ]

def is_same_team(char1: Character, char2: Character, turn_manager: TurnManager) -> bool:
    chars = [u for u in turn_manager.units if isinstance(u, Character)]
    cutoff = getattr(turn_manager, "player_team_size", len(chars) // 2)

    try:
        idx1 = chars.index(char1)
        idx2 = chars.index(char2)
    except ValueError:
        return False  # One or both chars no longer in list

    return (idx1 < cutoff and idx2 < cutoff) or (idx1 >= cutoff and idx2 >= cutoff)

def get_teams(turn_manager):
    """Splits characters into two teams using stored player_team_size."""
    chars = [u for u in turn_manager.units if isinstance(u, Character)]
    size = getattr(turn_manager, "player_team_size", len(chars) // 2)
    return chars[:size], chars[size:]

def get_living_allies(attacker: Character, turn_manager: TurnManager) -> list[Character]:
    return [
        ally for ally in get_allies(attacker, turn_manager)
        if isinstance(ally, Character) and ally.current_hp > 0
    ]

def get_living_enemies(attacker: Character, turn_manager: TurnManager) -> list[Character]:
    return [
        enemy for enemy in get_enemies(attacker, turn_manager)
        if isinstance(enemy, Character) and enemy.current_hp > 0
    ]

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
