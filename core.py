from dataclasses import dataclass, field
from collections import defaultdict, namedtuple
from typing import Optional, Callable, TYPE_CHECKING, Set
from elemental_enums import DamageType, Element, StatType, AuraTag
import uuid


if TYPE_CHECKING:
    from turn import TurnManager

NON_PERSISTENT_AURAS = {Element.ANEMO, Element.GEO, Element.QUANTUM, Element.PHYSICAL}

@dataclass
class ReactionInfo:
    elements: Set[Element]
    aura_name: str
    reaction_name: str
    faceup_element: Element
    locked: bool = False
    default_units: float = 1.0

REACTIONS_WITH_AURA = {
    frozenset({Element.DENDRO, Element.ELECTRO}): {
        "reaction_name": "Quicken",
        "aura_element": Element.DENDRO,
        "aura_name": "Quicken",
        "units": 1.0,
    },
    frozenset({Element.HYDRO, Element.CRYO}): {
        "reaction_name": "Frozen",
        "aura_element": Element.CRYO,
        "aura_name": "Frozen",
        "units": 1.0,
    },
    frozenset({Element.ELECTRO, Element.HYDRO}): {
        "reaction_name": "Electro-Charged",
        "aura_element": Element.ELECTRO,
        "aura_name": "Electro-Charged",
        "units": 1.0,
    },
    frozenset({Element.DENDRO, Element.PYRO}): {
        "reaction_name": "Burning",
        "aura_element": Element.PYRO,
        "aura_name": "Burning",
        "units": 1.0,
    },
    frozenset({Element.DENDRO, Element.CRYO}): {
        "reaction_name": "Rimegrass",
        "aura_element": Element.DENDRO,
        "aura_name": "Rimegrass",
        "units": 1.0,
    },
}

@dataclass
class ElementalApplicationResult:
    reaction: Optional[str] = None
    new_aura: Optional['Aura'] = None

@dataclass(unsafe_hash=True)
class Position:
    x: int
    y: int

class CombatUnit:
    def __init__(self, name: str, speed: int = 100):
        self.name = name
        self.speed = speed
        self.buffs = []
        self.debuffs = []
        self.turn_shifted = False

    def get_speed(self):
        return max(1, getattr(self, "speed", 100))

class ResistanceDict(defaultdict):
    def __missing__(self, key):
        return 0.1

@dataclass(unsafe_hash=True)
class Character(CombatUnit):
    name: str
    base_stats: dict = field(hash=False)
    element: Element
    stats: dict = field(init=False, hash=False)

    energy_pool: dict = field(default_factory=dict, hash=False)
    cooldowns: dict = field(default_factory=dict, hash=False)
    icd_trackers: dict = field(default_factory=dict, hash=False)
    icd_config: dict = field(default_factory=dict, hash=False)

    auras: list = field(default_factory=list, hash=False)
    buffs: list = field(default_factory=list, hash=False)
    debuffs: list = field(default_factory=list, hash=False)
    summons: list = field(default_factory=list, hash=False)
    frozen: bool = False
    current_form: Optional[str] = None
    turn_shifted: bool = False

    normal_attack_chain: Optional[Callable] = None
    skills: list = field(default_factory=list, hash=False)
    bursts: list = field(default_factory=list, hash=False)
    passives: list = field(default_factory=list, hash=False)
    combo_index: int = 0
    combo_chain: list = field(default_factory=list, hash=False)
    form_locked_normal_chains: dict = field(default_factory=dict, hash=False)

    elemental_bonuses: dict = field(default_factory=lambda: defaultdict(float), hash=False)
    type_bonuses: dict = field(default_factory=lambda: defaultdict(float), hash=False)
    general_dmg_bonus: float = 0.0
    dmg_reduction_taken: float = 0.0
    resistances: dict = field(default_factory=ResistanceDict, hash=False)
    level: int = 90

    max_hp: int = field(init=False, hash=False)
    current_hp: int = field(init=False, hash=False)

    position: Position = field(default_factory=lambda: Position(0, 0))

    def __post_init__(self):
        self.stats = self.base_stats.copy()
        self.max_hp = self.base_stats.get(StatType.HP, 15000)
        self.current_hp = self.max_hp

    def get_stat(self, stat: StatType):
        return self.stats.get(stat, 0)

    def add_talent(self, talent, category: str):
        if category == "skill":
            self.skills.append(talent)
        elif category == "burst":
            self.bursts.append(talent)

    def add_passive(self, passive):
        self.passives.append(passive)

    def add_combo_chain(self, talents: list):
        self.combo_chain = talents

    def set_normal_attack_chain(self, chain):
        self.normal_attack_chain = chain

    def get_active_normal_chain(self):
        if self.current_form in self.form_locked_normal_chains:
            return self.form_locked_normal_chains[self.current_form]
        return self.normal_attack_chain

    def set_form_locked_chain(self, form_name: str, chain):
        self.form_locked_normal_chains[form_name] = chain
    
    def get_resistance(self, element: Element) -> float:
        return self.resistances.get(element, 0.1)

    def apply_elemental_effect(self, element: Element, attacker: Optional['Character'] = None, units: float = 1.0, turn_manager: Optional['TurnManager'] = None):

        result = ElementalApplicationResult()

        current_auras = [a for a in self.auras if a.units > 0]

        for existing in current_auras:
            key = frozenset({element, existing.element})
            if key in REACTIONS_WITH_AURA:
                reaction_data = REACTIONS_WITH_AURA[key]

                # Remove both contributing elements
                self.auras = [a for a in self.auras if a.element not in key]

                new_aura = create_aura(
                    name=reaction_data["aura_name"],
                    element=reaction_data["aura_element"],
                    units=reaction_data["units"],
                    duration=2,
                    source_name=reaction_data["aura_name"],
                    source_elements=key
                )
                self.auras.append(new_aura)
                result.reaction = reaction_data["reaction_name"]
                result.new_aura = new_aura
                return result

        if element in NON_PERSISTENT_AURAS:
            return result
        
        if turn_manager and element in (Element.PYRO, Element.ELECTRO):
            from dendro_core import DendroCore, trigger_hyperbloom, trigger_burgeon
            for obj in turn_manager.field_objects:
                if isinstance(obj, DendroCore) and obj.active:
                    if self.position and obj.position:
                        if distance(self, obj.position) <= 1.5:
                            if element == Element.ELECTRO:
                                trigger_hyperbloom(obj, attacker or self, turn_manager)
                                result.reaction = "Hyperbloom"
                                return result
                            elif element == Element.PYRO:
                                trigger_burgeon(obj, attacker or self, turn_manager)
                                result.reaction = "Burgeon"
                                return result

        existing = next((a for a in self.auras if a.element == element), None)
        if existing:
            existing.units = max(existing.units, units)
            existing.duration = 2
            result.new_aura = existing
        else:
            new_aura = create_aura(name=element.name, element=element, units=units, duration=2, source_name=None)
            self.auras.append(new_aura)
            result.new_aura = new_aura

        return result

    def decay_auras(self):
        remaining_auras = []
        for aura in self.auras:
            expired = aura.decay()
            if not expired:
                remaining_auras.append(aura)
            else:
                print(f"{aura.name} aura on {self.name} has expired.")
        self.auras = remaining_auras

class DendroCore:
    def __init__(self, creator: Character, position: Position):
        self.creator = creator
        self.position = position
        self.remaining_turns = 3  # Or time-to-live
        self.is_active = True

@dataclass
class Aura:
    name: str
    element: 'Element'  # Face-up element
    units: float = 1.0
    duration: int = 2
    decay_rate: float = 0.3
    source: Optional['Character'] = None
    locked: bool = False
    source_elements: Set['Element'] = field(default_factory=set)
    tags: set[AuraTag] = field(default_factory=set)

    def decay(self) -> bool:
        if self.duration > 0:
            self.duration -= 1
        else:
            self.units = max(0.0, self.units - self.decay_rate)
        return self.is_expired()

    def is_expired(self) -> bool:
        return self.units <= 0.0 or self.duration <= 0
    
    def is_composite(self) -> bool:
        return len(self.source_elements) > 1
    
    def add_tag(self, tag: AuraTag):
        self.tags.add(tag)

    def has_tag(self, tag: AuraTag) -> bool:
        return tag in self.tags

    def has_any_tag(self, tag_set: set[AuraTag]) -> bool:
        return any(tag in self.tags for tag in tag_set)

    def remove_tag(self, tag: AuraTag):
        self.tags.discard(tag)

SPECIAL_AURA_TAGS = {
    "Quicken": AuraTag.QUICKEN,
    "Frozen": AuraTag.FROZEN,
    "Burning": AuraTag.BURNING,
    "Electro-Charged": AuraTag.ELECTRO_CHARGED,
    "Rimegrass": AuraTag.RIMEGRASS,
}

def create_aura(
    name: str,
    element: Element,
    units: float = 1.0,
    duration: int = 2,
    source_name: Optional[str] = None,
    locked: bool = False,
    source_elements: Optional[frozenset[Element]] = None
) -> Aura:
    aura = Aura(
        name=name,
        element=element,
        units=units,
        duration=duration,
        locked=locked,
        source_elements=source_elements,
    )

    tag = SPECIAL_AURA_TAGS.get(source_name)
    if tag:
        aura.add_tag(tag)
    return aura

class DamageInstance:
    def __init__(self, multiplier: float, scaling_stat: StatType, damage_type: DamageType,
                 base_dmg_multiplier: float = 1.0, additive_base_dmg_bonus: float = 0.0,
                 element: Element | None = None, description: str = "", tag: str = "",
                 icd_tag: str = "", icd_interval: int = 3, aoe_radius: float = 0.0):
        self.multiplier = multiplier
        self.scaling_stat = scaling_stat
        self.damage_type = damage_type
        self.base_dmg_multiplier = base_dmg_multiplier
        self.additive_base_dmg_bonus = additive_base_dmg_bonus
        self.element = element
        self.description = description
        self.tag = tag
        self.icd_tag = icd_tag
        self.icd_interval = icd_interval
        self.aoe_radius = aoe_radius

class Talent:
    def __init__(self, name, description: str = "", damage_instances=None, energy_type="normal",
                 energy_cost=0, cooldown=0, on_use=None, form_lock=None):
        self.name = name
        self.description = description
        self.damage_instances = damage_instances if damage_instances else []
        self.energy_type = energy_type
        self.energy_cost = energy_cost
        self.cooldown = cooldown
        self.on_use = on_use if isinstance(on_use, list) else [on_use] if on_use else []
        self.form_lock = form_lock
        self.id = uuid.uuid4()

class Passive:
    def __init__(self, name: str, description: str, trigger, effect):
        self.name = name
        self.description = description
        self.trigger = trigger
        self.effect = effect

    def activate(self, **kwargs):
        return self.effect(**kwargs)

class Summon(CombatUnit):
    def __init__(self, name: str, owner: Character, stats: dict, hp: int, triggers: dict[str, callable], duration: int = None, is_stationary=False, speed=100, talents: list = None):
        super().__init__(name, speed)
        self.owner = owner
        self.stats = stats
        self.max_hp = hp
        self.current_hp = hp
        self.triggers = triggers
        self.duration = duration
        self.remaining_duration = duration
        self.is_stationary = is_stationary
        self.frozen = False
        self.talents = []
        self.passives = []

    def get_stat(self, stat):
        return self.stats.get(stat, 0)

    def handle_event(self, event_name: str, **kwargs):
        if event_name in self.triggers:
            self.triggers[event_name](self, **kwargs)

class NormalAttackChain:
    def __init__(self, name: str, talents: list[Talent]):
        self.name = name
        self.talents = talents

    def get_talent(self, index: int) -> Talent:
        return self.talents[index % len(self.talents)]

    def length(self):
        return len(self.talents)

def get_speed(unit):
    if hasattr(unit, 'speed'):
        return max(1, getattr(unit, "speed", 100))
    if hasattr(unit, 'get_stat'):
        return max(1, unit.get_stat(StatType.SPD))
    return 100  # generic fallback

def distance(a: Character, b: Character) -> float:
    dx = a.position.x - b.position.x
    dy = a.position.y - b.position.y
    return (dx ** 2 + dy ** 2) ** 0.5  # Euclidean distance

def place_in_grid(units: list[Character], columns: int = 3, spacing: int = 1, start_x: int = 0, start_y: int = 0):
    for i, unit in enumerate(units):
        x = start_x + (i % columns) * spacing
        y = start_y + (i // columns) * spacing
        unit.position = Position(x=x, y=y)
