from core import *
from reaction_logic import *
from constants import *
import random
from reaction_constants import *
from position_utils import *

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

            reaction_result_data = resolve_reaction_effect(reaction_name, attacker, defender, turn_manager)
            reaction_hits.extend(reaction_result_data)

            emoji = REACTION_EMOJIS.get(reaction_name, "💥")
            print(f"{emoji} {reaction_name} triggered by {attacker.name}!")

            reaction_hit_exists = any(isinstance(r, ReactionHit) and is_transformative(r.reaction) for r in reaction_result_data)
            if is_transformative(reaction_name) and not reaction_hit_exists:
                reaction_result = calculate_transformative_damage(
                    reaction_name, attacker, source_elements=reacted_with_aura.source_elements if reacted_with_aura else None
                )
                
                # Primary hit
                reaction_hits.append(ReactionHit(
                    source=attacker,
                    target=defender,
                    reaction=reaction_result["label"],
                    damage=reaction_result["damage"],
                    element=reaction_result["element"]
                ))

                # AoE splash
                aoe_radius = reaction_result.get("aoe_radius", 0.0)
                if aoe_radius > 0:
                    all_enemies = get_enemies(attacker, turn_manager)
                    splash_targets = get_targets_in_radius(defender, all_enemies, aoe_radius)
                    for target in splash_targets:
                        if target == defender:
                            continue
                        reaction_hits.append(ReactionHit(
                            source=attacker,
                            target=target,
                            reaction=f"{reaction_result['label']} (Splash)",
                            damage=reaction_result["damage"],
                            element=reaction_result["element"]
                        ))

            if is_amplifying(reaction_name):
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
