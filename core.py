from enum import Enum, auto
from dataclasses import dataclass, field
from collections import defaultdict
from typing import Optional, Callable
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
    resistances: dict = field(default_factory=lambda: defaultdict(float), hash=False)
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

    def apply_elemental_effect(self, element: Element, attacker: Optional['Character'] = None, icd_tag: str = None, icd_interval: int = 3, units: float = 1.0):

        current_elements = {aura.element for aura in self.auras if aura.units > 0}

        if (element == Element.DENDRO and Element.ELECTRO in current_elements) or \
            (element == Element.ELECTRO and Element.DENDRO in current_elements):
            self.auras = [a for a in self.auras if a.element not in (Element.DENDRO, Element.ELECTRO)]
            self.auras.append(Aura("Quicken", Element.DENDRO, units=1.0, locked=True))
            print(f"{self.name} is now affected by Quicken.")
            return

        if (element == Element.HYDRO and Element.CRYO in current_elements) or \
            (element == Element.CRYO and Element.HYDRO in current_elements):
            self.auras = [a for a in self.auras if a.element not in (Element.HYDRO, Element.CRYO)]
            self.auras.append(Aura("Frozen", Element.CRYO, units=1.0, locked=True))
            print(f"{self.name} is now Frozen.")
            return

        if (element == Element.ELECTRO and Element.HYDRO in current_elements) or \
            (element == Element.HYDRO and Element.ELECTRO in current_elements):
            self.auras = [a for a in self.auras if a.element not in (Element.ELECTRO, Element.HYDRO)]
            self.auras.append(Aura("Electro-Charged", Element.ELECTRO, units=1.0, locked=True))
            print(f"{self.name} is now Electro-Charged.")
            return

        if (element == Element.CRYO and Element.DENDRO in current_elements) or \
           (element == Element.DENDRO and Element.CRYO in current_elements):
            self.auras = [a for a in self.auras if a.element not in (Element.CRYO, Element.DENDRO)]
            self.auras.append(Aura("Frost-Twined", Element.CRYO, units=1.0, locked=True))
            print(f"{self.name} is now Frost-Twined.")
            return

        existing = next((a for a in self.auras if a.element == element), None)

        if existing:
            if existing.locked:
                print(f"{self.name} already has a locked {element.name} aura. No new units applied.")
                return
            existing.duration = max(existing.duration, 2)
            print(f"{element.name} aura on {self.name} refreshed to {existing.units}U.")
        else:
            self.auras.append(Aura(name=element.name, element=element, units=units))
            print(f"{element.name} {units}U aura applied to {self.name}.")

        if element in NON_PERSISTENT_AURAS and not existing:
            print(f"{element.name} is a non-persistent aura. Skipping.")
            return

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

class Aura:
    def __init__(self, name: str, element: Element, units: float = 1.0, duration: int = 2, decay_rate: float = 0.5, source: Optional[Character] = None, locked: bool = False):
        self.name = name
        self.element = element
        self.units = units
        self.duration = duration
        self.decay_rate = decay_rate
        self.source = source
        self.locked = locked

    def decay(self):
        self.units = max(0.0, self.units - self.decay_rate)
        self.duration -= 1
        return self.is_expired()

    def is_expired(self):
        return self.units <= 0.0 or self.duration <= 0

NON_PERSISTENT_AURAS = {Element.ANEMO, Element.GEO, Element.QUANTUM, Element.IMAGINARY, Element.PHYSICAL}

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
