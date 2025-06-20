from enum import Enum, auto

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
