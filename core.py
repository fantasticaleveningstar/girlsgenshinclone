from enum import Enum, auto
from dataclasses import dataclass, field
from collections import defaultdict, namedtuple
from typing import Optional, Callable, Set
import uuid

class Element(Enum):
    PHYSICAL = auto()
    PYRO = auto()
    HYDRO = auto()
    ELECTRO = auto()
    CRYO = auto()
    GEO = auto()
    ANEMO = auto()
    DENDRO = auto()
    QUANTUM = auto()
    IMAGINARY = auto()

class AuraTag(Enum):
    QUICKEN = auto()
    FROZEN = auto()
    BURNING = auto()
    ELECTRO_CHARGED = auto()
    RIMEGRASS = auto()
    # You can add others here

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
        "locked": True,
        "units": 1.0,
    },
    frozenset({Element.HYDRO, Element.CRYO}): {
        "reaction_name": "Frozen",
        "aura_element": Element.CRYO,
        "aura_name": "Frozen",
        "locked": True,
        "units": 1.0,
    },
    frozenset({Element.ELECTRO, Element.HYDRO}): {
        "reaction_name": "Electro-Charged",
        "aura_element": Element.ELECTRO,
        "aura_name": "Electro-Charged",
        "locked": True,
        "units": 1.0,
    },
    frozenset({Element.DENDRO, Element.PYRO}): {
        "reaction_name": "Burning",
        "aura_element": Element.PYRO,
        "aura_name": "Burning",
        "locked": True,
        "units": 1.0,
    },
    frozenset({Element.DENDRO, Element.CRYO}): {
        "reaction_name": "Rimegrass",
        "aura_element": Element.DENDRO,
        "aura_name": "Rimegrass",
        "locked": True,
        "units": 1.0,
    },
}

@dataclass
class ElementalApplicationResult:
    reaction: Optional[str] = None
    new_aura: Optional['Aura'] = None

class DamageType(Enum):
    NORMAL_ATTACK = auto()
    CHARGED_ATTACK = auto()
    SKILL = auto()
    BURST = auto()
    REACTION = auto()

class StatType(Enum):
    ATK = auto()
    DEF = auto()
    HP = auto()
    EM = auto()
    SPD = auto()
    CRIT_RATE = auto()
    CRIT_DMG = auto()
    ENERGY_RECHARGE = auto()

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

    def apply_elemental_effect(self, element: Element, attacker: Optional['Character'] = None, units: float = 1.0):

        result = ElementalApplicationResult()

        current_auras = [a for a in self.auras if a.units > 0]

        for existing in current_auras:
            key = frozenset({element, existing.element})
            if key in REACTIONS_WITH_AURA:
                reaction_data = REACTIONS_WITH_AURA[key]

                # Remove both contributing elements
                self.auras = [a for a in self.auras if a.element not in key]

                # Apply locked composite aura
                new_aura = Aura(
                    name=reaction_data["aura_name"],
                    element=reaction_data["aura_element"],
                    units=reaction_data["units"],
                    locked=reaction_data["locked"],
                    source_elements=key
                )
                self.auras.append(new_aura)
                result.reaction = reaction_data["reaction_name"]
                result.new_aura = new_aura
                return result

        existing = next((a for a in self.auras if a.element == element), None)
        if existing:
            if existing.locked:
                print(f"{self.name} already has a locked {element.name} aura.")
                return result
            existing.units = max(existing.units, units)
            existing.duration = 2
            result.new_aura = existing
        else:
            new_aura = Aura(name=element.name, element=element, units=units)
            self.auras.append(new_aura)
            result.new_aura = new_aura

        return result

    def decay_auras(self):
        remaining_auras = []
        for aura in self.auras:
            if aura.locked:
                remaining_auras.append(aura)
                continue
            expired = aura.decay()
            if not expired:
                remaining_auras.append(aura)
            else:
                print(f"{aura.name} aura on {self.name} has expired.")
        self.auras = remaining_auras

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

class DamageInstance:
    def __init__(self, multiplier: float, scaling_stat: StatType, damage_type: DamageType,
                 base_dmg_multiplier: float = 1.0, additive_base_dmg_bonus: float = 0.0,
                 element: Element | None = None, description: str = "", tag: str = "",
                 icd_tag: str = "", icd_interval: int = 3):
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
