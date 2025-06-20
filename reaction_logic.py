from core import *
from turn import *
from combat_helpers import *
from constants import *
from reaction_constants import *
from dendro_core import spawn_dendro_core

class ReactionHit:
    def __init__(self, source: Character, target: Character, reaction: str, damage: float, element: Element):
        self.source = source
        self.target = target
        self.reaction = reaction
        self.damage = damage
        self.element = element
    
    def resolve(self):
        print(f"{self.reaction} deals {int(self.damage)} damage to {self.target.name}!")

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
        (Element.CRYO, Element.ANEMO): "Cryo Swirl",
        (Element.PYRO, Element.ANEMO): "Pyro Swirl",
        (Element.HYDRO, Element.ANEMO): "Anemo Swirl",
        (Element.ELECTRO, Element.ANEMO): "Electro Swirl",
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

def calculate_amplifying_damage(reaction: str, attacker: Character) -> float:
    em = attacker.get_stat(StatType.EM)
    base_multi = get_amplifying_multiplier(reaction)
    if reaction == "Superposition":
        em_multi = 1.28
    else:
        em_multi = 2.78
    return base_multi * (1 + (em_multi * (em)/(1400 + em)))

def calculate_transformative_damage(reaction: str, attacker: Character, source_elements: Optional[frozenset[Element]] = None) -> float:
    aoe_radius = 0.0
    em = attacker.get_stat(StatType.EM)
    base_damage = 1446 
    em_bonus = 1 + (16 * em / (em + 2000))
    final_damage = base_damage * em_bonus * get_transformative_multiplier(reaction)

    if reaction in ["Bloom", "Hyperbloom", "Burgeon"]:
        element = Element.DENDRO
        aoe_radius = 2.0
    elif reaction in ["Overload", "Burning"]:
        element = Element.PYRO
        aoe_radius = 2.0
    elif reaction == "Electro-Charged":
        element = Element.ELECTRO
        aoe_radius = 0.0
    elif reaction == "Superconduct":
        element = Element.CRYO
        aoe_radius = 1.5
    elif reaction == "Pyro Swirl":
        element = Element.PYRO
        aoe_radius = 3.0
    elif reaction == "Cryo Swirl":
        element = Element.CRYO
        aoe_radius = 3.0
    elif reaction == "Hydro Swirl":
        element = Element.HYDRO
        aoe_radius = 3.0
    elif reaction == "Electro Swirl":
        element = Element.ELECTRO
        aoe_radius = 3.0
    elif reaction == "Shatter":
        element = Element.PHYSICAL
        aoe_radius = 0.0
    elif reaction in ["Stasis", "Ignition", "Impulse", "Anchor"]:
        element = Element.IMAGINARY
        aoe_radius = 0.0
    elif reaction == "Superposition" and source_elements:
        element = random.choice(list(source_elements))
        aoe_radius = 2.0
        superposition_hit = {
            "damage": int(final_damage),
            "element": element,
            "label": reaction,
            "crit": True,
            "aoe_radius": aoe_radius 
        }
        return superposition_hit
    else:
        element = Element.PHYSICAL  # fallback

    return {
        "damage": int(final_damage),
        "element": element,
        "label": reaction,
        "crit": False,
        "aoe_radius": aoe_radius
    }

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
    
    elif reaction == "Bloom":
        spawn_dendro_core(attacker, defender, turn_manager)

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

def is_consuming_reaction(reaction: str) -> bool:
    return reaction not in ("Quicken", "Aggravate", "Spread", "Freeze", "Electro-Charged", "Burning")

def consume_aura_units(defender: Character, element: Element, reaction: str = None):
    units_to_consume = REACTION_AURA_CONSUMPTION.get(reaction, 1.0)

    for aura in defender.auras:
        print(f"[DEBUG] {element.name} aura on {defender.name} has {aura.units:.2f}U before consumption")
        if aura.element == element:
            aura.units = max(0, aura.units - units_to_consume)
            if aura.units <= 0:
                print(f"{element.name} aura on {defender.name} fully consumed.")
                defender.auras.remove(aura)
            else:
                print(f"{units_to_consume}U of {element.name} aura consumed. Remaining: {aura.units:.2f}U")
            break

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
