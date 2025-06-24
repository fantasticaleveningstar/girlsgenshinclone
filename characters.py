from enum import Enum, auto
import random
import heapq
import itertools
import uuid
from dataclasses import dataclass, field
from collections import defaultdict
from typing import Optional, Callable
from core import Character, StatType, Element, DamageInstance, DamageType, Talent, NormalAttackChain, Passive
from turn import TurnManager, Buff
from combat import summon_salon_members, heal, get_allies

#yanfei core
yanfei = Character("Yanfei",
                   base_stats={
                       StatType.ATK: 2400,
                       StatType.DEF: 800,
                       StatType.HP: 14000,
                       StatType.SPD: 85,
                       StatType.CRIT_RATE: 0.75,
                       StatType.CRIT_DMG: 1.5,
                       StatType.EM: 500,
                       StatType.ENERGY_RECHARGE: 1.0,
                       },
                       element=Element.PYRO
                   )

seal_of_approval = NormalAttackChain(
    name="Seal of Approval",
    talents=[
        Talent(
            name="Seal of Approval N1",
            description="Yanfei N1",
            damage_instances=[
                DamageInstance(
                    multiplier=0.992,
                    scaling_stat=StatType.ATK,
                    damage_type=DamageType.NORMAL_ATTACK,
                    element=Element.PYRO,
                    tag="Yanfei Normal Attack",
                    icd_interval=3)
            ]
                ),
        Talent(
            name="Seal of Approval N2",
            description="Yanfei N2",
            damage_instances=[
                DamageInstance(
                    multiplier=0.886,
                    scaling_stat=StatType.ATK,
                    damage_type=DamageType.NORMAL_ATTACK,
                    element=Element.PYRO,
                    tag="Yanfei Normal Attack",
                    icd_interval=3)
            ]
                ),
        Talent(
            name="Seal of Approval N3",
            description="Yanfei N3",
            damage_instances=[
                DamageInstance(
                    multiplier=1.292,
                    scaling_stat=StatType.ATK,
                    damage_type=DamageType.NORMAL_ATTACK,
                    element=Element.PYRO,
                    tag="Yanfei Normal Attack",
                    icd_interval=3)
            ]
                ),
            
        ]
)

signed_edict = Talent(
    name="Signed Edict",
    description="Yanfei Skill",
    damage_instances=[
        DamageInstance(multiplier=2.88,
                       scaling_stat=StatType.ATK,
                       damage_type=DamageType.SKILL,
                       element=Element.PYRO,
                       )
    ]
)

done_deal = Talent(
    name="Done Deal",
    description="Yanfei Burst",
    damage_instances=[
        DamageInstance(multiplier=3.10,
                       scaling_stat=StatType.ATK,
                       damage_type=DamageType.BURST,
                       element=Element.PYRO,
                       )
    ]
)

yanfei.set_normal_attack_chain(seal_of_approval)
yanfei.add_talent(done_deal, "burst")
yanfei.add_talent(signed_edict, "skill")

#shinobu core
shinobu = Character("Shinobu",
                   base_stats={
                       StatType.ATK: 1200,
                       StatType.DEF: 1400,
                       StatType.HP: 27346,
                       StatType.SPD: 100,
                       StatType.CRIT_RATE: 1,
                       StatType.CRIT_DMG: 2.268,
                       StatType.EM: 300,
                       StatType.ENERGY_RECHARGE: 1.0,
                       },
                       element=Element.ELECTRO)
                    
def shinobu_heal(attacker: Character, defender: Character, turn_manager: TurnManager, **kwargs):
    heal_amount = int(0.15 * attacker.get_stat(StatType.HP))
    team = kwargs.get("team", [])
    actual = heal(target=attacker, amount=heal_amount, source=attacker, team=team)
    return 0, []

kariyama_rite = Talent(
    name="Gyoei Narukami Kariyama Rite",
    description="1 big hit + 3 smaller + self-heal",
    damage_instances=[
        DamageInstance(multiplier=0.1, scaling_stat=StatType.HP, damage_type=DamageType.SKILL,
                       element=Element.ELECTRO, description="Initial Electro Strike", icd_tag="ShinobuBurst", icd_interval=3),
        DamageInstance(multiplier=0.067, scaling_stat=StatType.HP, damage_type=DamageType.SKILL,
                       element=Element.ELECTRO, description="Electro Pulse 1", icd_tag="ShinobuBurst", icd_interval=3),
        DamageInstance(multiplier=0.067, scaling_stat=StatType.HP, damage_type=DamageType.SKILL,
                       element=Element.ELECTRO, description="Electro Pulse 2", icd_tag="ShinobuBurst", icd_interval=3),
        DamageInstance(multiplier=0.067, scaling_stat=StatType.HP, damage_type=DamageType.SKILL,
                       element=Element.ELECTRO, description="Electro Pulse 3", icd_tag="ShinobuBurst", icd_interval=3),
        DamageInstance(multiplier=0.067, scaling_stat=StatType.HP, damage_type=DamageType.SKILL,
                       element=Element.ELECTRO, description="Electro Pulse 4", icd_tag="ShinobuBurst", icd_interval=3),
        DamageInstance(multiplier=0.067, scaling_stat=StatType.HP, damage_type=DamageType.SKILL,
                       element=Element.ELECTRO, description="Electro Pulse 5", icd_tag="ShinobuBurst", icd_interval=3),
        DamageInstance(multiplier=0.067, scaling_stat=StatType.HP, damage_type=DamageType.SKILL,
                       element=Element.ELECTRO, description="Electro Pulse 6", icd_tag="ShinobuBurst", icd_interval=3),
        DamageInstance(multiplier=0.067, scaling_stat=StatType.HP, damage_type=DamageType.SKILL,
                       element=Element.ELECTRO, description="Electro Pulse 7", icd_tag="ShinobuBurst", icd_interval=3),
        DamageInstance(multiplier=0.067, scaling_stat=StatType.HP, damage_type=DamageType.SKILL,
                       element=Element.ELECTRO, description="Electro Pulse 8", icd_tag="ShinobuBurst", icd_interval=3),
    ],
    on_use=[shinobu_heal],
    energy_type="Electro"
)

shinobu.add_talent(kariyama_rite, "burst")

#furina core
furina = Character("Furina",
                   base_stats={
                       StatType.ATK: 1100,
                       StatType.DEF: 900,
                       StatType.HP: 35000,
                       StatType.SPD: 110,
                       StatType.CRIT_RATE: 0.6,
                       StatType.CRIT_DMG: 1.8,
                       StatType.EM: 0,
                       StatType.ENERGY_RECHARGE: 1.6,
                       },
                       element=Element.HYDRO
)

furina.summon_turn_counter = 3  # or whatever lifespan you want

def decrement_summon_duration(furina: Character, turn_manager: TurnManager):
    if hasattr(furina, "summon_turn_counter"):
        furina.summon_turn_counter -= 1
        if furina.summon_turn_counter <= 0:
            for summon in list(furina.summons):
                print(f"{summon.name} expires as Furina's counter ends.")
                furina.summons.remove(summon)
                if summon in turn_manager.units:
                    turn_manager.units.remove(summon)
                turn_manager.timeline = [(t, o, c) for (t, o, c) in turn_manager.timeline if c != summon]
                heapq.heapify(turn_manager.timeline)

soloists_solicitation = NormalAttackChain(
    name="Soloist's Solicitation",
    talents=[
        Talent(
            name="Soloist's Solicitation N1",
            description="Furina N1",
            damage_instances=[
                DamageInstance(
                    multiplier=0.889,
                    scaling_stat=StatType.ATK,
                    damage_type=DamageType.NORMAL_ATTACK,
                    element=Element.PHYSICAL,
                    tag="Furina Normal Attack",
                    icd_interval=3)
            ]
                ),
        Talent(
            name="Soloist's Solicitation N2",
            description="Furina N2",
            damage_instances=[
                DamageInstance(
                    multiplier=0.803,
                    scaling_stat=StatType.ATK,
                    damage_type=DamageType.NORMAL_ATTACK,
                    element=Element.PHYSICAL,
                    tag="Furina Normal Attack",
                    icd_interval=3)
            ]
                ),
        Talent(
            name="Soloist's Solicitation N3",
            description="Furina N3",
            damage_instances=[
                DamageInstance(
                    multiplier=1.013,
                    scaling_stat=StatType.ATK,
                    damage_type=DamageType.NORMAL_ATTACK,
                    element=Element.PHYSICAL,
                    tag="Furina Normal Attack",
                    icd_interval=3)
            ]
                ),

        Talent(
            name="Soloist's Solicitation N4",
            description="Furina N4",
            damage_instances=[
                DamageInstance(
                    multiplier=1.347,
                    scaling_stat=StatType.ATK,
                    damage_type=DamageType.NORMAL_ATTACK,
                    element=Element.PHYSICAL,
                    tag="Furina Normal Attack",
                    icd_interval=3)
            ]
                ),
        ]
)

salon_solitaire = Talent(
    name="Salon Solitaire",
    description="Summons either the Salon Members or Singer of Many Waters.",
    damage_instances=[
        DamageInstance(multiplier=0.134,
                       scaling_stat=StatType.HP,
                       damage_type=DamageType.SKILL,
                       element=Element.HYDRO,
                       )
    ],
    cooldown=5,
    on_use=summon_salon_members,
)

furina.fanfare_points = 0

def gain_fanfare_from_hp_change(observer: Character, unit: Character, old_hp: int, new_hp: int):
    if not hasattr(observer, "fanfare_points") or not getattr(observer, "revelry_active", False):
        return

    # Only gain fanfare if the party-wide duration buff is active
    active_timer = getattr(observer, "revelry_timer", None)
    if not active_timer or active_timer.remaining_turns <= 0:
        return

    if unit.current_hp <= 0 or unit.max_hp == 0:
        return

    delta = abs(new_hp - old_hp)
    percent_change = (delta / unit.max_hp) * 100
    points_gained = int(percent_change)

    if points_gained > 0:
        observer.fanfare_points += points_gained
        print(f"{observer.name} gains {points_gained} Fanfare (total: {observer.fanfare_points}) from {unit.name}'s HP change.")
        refresh_universal_revelry_bonuses(observer)

def update_party_revelry_bonuses(buff: Buff, unit: Character, **kwargs):
    source = buff.source
    if not hasattr(source, "fanfare_points"):
        print(f"[DEBUG] {unit.name} → missing source fanfare.")
        return

    bonus_pct = source.fanfare_points * 0.0023  
    healing_bonus = source.fanfare_points * 0.0009 
    unit.general_dmg_bonus = bonus_pct
    print(f"{unit.name} receives {bonus_pct*100:.1f}% DMG bonus from Universal Revelry.")

def refresh_universal_revelry_bonuses(furina: Character):
    print(f"[DEBUG] refresh_universal_revelry_bonuses called for {furina.name}")
    if not getattr(furina, "revelry_active", False):
        return

    for unit in getattr(furina, "revelry_units", []):
        for buff in unit.buffs:
            if buff.name == "Universal Revelry" and buff.source == furina:
                update_party_revelry_bonuses(buff, unit)

def expire_universal_revelry(furina: Character):
    print(f"Universal Revelry has expired.")

    for unit in getattr(furina, "revelry_units", []):
        unit.buffs = [b for b in unit.buffs if not (b.name == "Universal Revelry" and b.source == furina)]
        unit.general_dmg_bonus = 0

    furina.fanfare_points = 0
    furina.revelry_active = False

def apply_universal_revelry(attacker: Character, defender: Character, turn_manager, team: list[Character]):
    print(f"{attacker.name} activates Universal Revelry!")

    attacker.fanfare_points = 0  # Reset fanfare
    attacker.revelry_units = []  # Track affected allies
    attacker.revelry_active = True

    # Manually apply the buff to each teammate
    for unit in team:
        if unit.current_hp <= 0:
            continue

        unit.buffs = [b for b in unit.buffs if not (b.name == "Universal Revelry" and b.source == attacker)]

        buff = Buff(
            name="Universal Revelry",
            description="Gain DMG and Healing Bonus based on Fanfare.",
            duration=3,
            trigger="on_turn_start",
            source=attacker,
            effect=update_party_revelry_bonuses,
            cleanup_effect=lambda char: setattr(char, "general_dmg_bonus", 0),
            reversible=True
        )

        unit.buffs.append(buff)
        attacker.revelry_units.append(unit)

    # Add shared timer
    duration_buff = Buff(
        name="Universal Revelry Duration",
        description="Party-wide timer for Universal Revelry.",
        duration=3,
        source=attacker,
        reversible=False,
        trigger="on_turn_start",
        effect=None,
        cleanup_effect=expire_universal_revelry
    )
    attacker.revelry_timer = duration_buff
    turn_manager.add_buff_timer(duration_buff, attacker)

    return 0, []

people_rejoice = Talent(
    name="Let the People Rejoice",
    description="Lets her name echo in song.",
    damage_instances=[
        DamageInstance(multiplier=0.194,
                       scaling_stat=StatType.HP,
                       damage_type=DamageType.BURST,
                       element=Element.HYDRO,
                       )
    ],
    cooldown=3,
    on_use=apply_universal_revelry
)

fanfare_tracker = Passive(
    name="Fanfare Tracker",
    description="Gain Fanfare when party HP changes.",
    trigger="on_hp_change",
    effect=gain_fanfare_from_hp_change
)

furina.set_normal_attack_chain(soloists_solicitation)
furina.add_talent(salon_solitaire, "skill")
furina.add_talent(people_rejoice, "burst")
furina.add_passive(fanfare_tracker)

#rosaria core
rosaria = Character("Rosaria",
                   base_stats={
                       StatType.ATK: 2400,
                       StatType.DEF: 900,
                       StatType.HP: 18000,
                       StatType.SPD: 120,
                       StatType.CRIT_RATE: 1,
                       StatType.CRIT_DMG: 1.8,
                       StatType.EM: 200,
                       StatType.ENERGY_RECHARGE: 1.0,
                       },
                       element=Element.CRYO
                   )

church_spear = NormalAttackChain(
    name="Spear of the Church",
    talents=[
        Talent(
            name="Spear of the Church N1",
            description="Rosaria N1",
            damage_instances=[
                DamageInstance(
                    multiplier=0.964,
                    scaling_stat=StatType.ATK,
                    damage_type=DamageType.NORMAL_ATTACK,
                    element=Element.PHYSICAL,
                    tag="Rosaria Normal Attack",
                    icd_interval=3)
            ]
                ),
        Talent(
            name="Spear of the Church N2",
            description="Rosaria N2",
            damage_instances=[
                DamageInstance(
                    multiplier=0.948,
                    scaling_stat=StatType.ATK,
                    damage_type=DamageType.NORMAL_ATTACK,
                    element=Element.PHYSICAL,
                    tag="Rosaria Normal Attack",
                    icd_interval=3)
            ]
                ),
        Talent(
            name="Spear of the Church N3",
            description="Rosaria N3",
            damage_instances=[
                DamageInstance(
                    multiplier=0.585,
                    scaling_stat=StatType.ATK,
                    damage_type=DamageType.NORMAL_ATTACK,
                    element=Element.PHYSICAL,
                    tag="Rosaria Normal Attack",
                    icd_interval=3),
                DamageInstance(
                    multiplier=0.585,
                    scaling_stat=StatType.ATK,
                    damage_type=DamageType.NORMAL_ATTACK,
                    element=Element.PHYSICAL,
                    tag="Rosaria Normal Attack",
                    icd_interval=3)
            ]
                ),
        Talent(
            name="Spear of the Church N4",
            description="Rosaria N4",
            damage_instances=[
                DamageInstance(
                    multiplier=1.38,
                    scaling_stat=StatType.ATK,
                    damage_type=DamageType.NORMAL_ATTACK,
                    element=Element.PHYSICAL,
                    tag="Rosaria Normal Attack",
                    icd_interval=3)
            ]
                ),
        Talent(
            name="Spear of the Church N5",
            description="Rosaria N5",
            damage_instances=[
                DamageInstance(
                    multiplier=0.765,
                    scaling_stat=StatType.ATK,
                    damage_type=DamageType.NORMAL_ATTACK,
                    element=Element.PHYSICAL,
                    tag="Rosaria Normal Attack",
                    icd_interval=3),
                DamageInstance(
                    multiplier=0.9,
                    scaling_stat=StatType.ATK,
                    damage_type=DamageType.NORMAL_ATTACK,
                    element=Element.PHYSICAL,
                    tag="Rosaria Normal Attack",
                    icd_interval=3),
            ]
                ),
        ]
)

ravaging_confession = Talent(
    name="Ravaging Confession",
    description="Rosaria's skill.",
    damage_instances=[
        DamageInstance(multiplier=0.99,
                       scaling_stat=StatType.ATK,
                       damage_type=DamageType.SKILL,
                       element=Element.CRYO,
                       ),
        DamageInstance(multiplier=2.31,
                       scaling_stat=StatType.ATK,
                       damage_type=DamageType.SKILL,
                       element=Element.CRYO,
                       )
    ],
    cooldown=1
)

rites_of_termination = Talent(
    name="Rites of Termination",
    description="Rosaria's burst.",
    damage_instances=[
        DamageInstance(multiplier=1.77,
                       scaling_stat=StatType.ATK,
                       damage_type=DamageType.BURST,
                       element=Element.CRYO,
                       ),
        DamageInstance(multiplier=2.58,
                       scaling_stat=StatType.ATK,
                       damage_type=DamageType.BURST,
                       element=Element.CRYO,
                       ),
        DamageInstance(multiplier=2.24,
                       scaling_stat=StatType.ATK,
                       damage_type=DamageType.BURST,
                       element=Element.CRYO,
                       ),
    ],
    cooldown=3
)

rosaria.set_normal_attack_chain(church_spear)
rosaria.add_talent(ravaging_confession, "skill")
rosaria.add_talent(rites_of_termination, "burst")

#gaming core
gaming = Character("Gaming",
                   base_stats={
                       StatType.ATK: 1600,
                       StatType.DEF: 900,
                       StatType.HP: 18000,
                       StatType.SPD: 130,
                       StatType.CRIT_RATE: 1,
                       StatType.CRIT_DMG: 1.8,
                       StatType.EM: 300,
                       StatType.ENERGY_RECHARGE: 1.0,
                       },
                       element=Element.QUANTUM
                   )

stellar_rend = NormalAttackChain(
    name="Stellar Rend",
    talents=[
        Talent(
            name="Stellar Rend N1",
            description="Gaming N1",
            damage_instances=[
                DamageInstance(
                    multiplier=1.541,
                    scaling_stat=StatType.ATK,
                    damage_type=DamageType.NORMAL_ATTACK,
                    element=Element.PHYSICAL,
                    tag="Gaming Normal Attack",
                    icd_interval=3)
            ]
                ),
        Talent(
            name="Stellar Rend N2",
            description="Gaming N2",
            damage_instances=[
                DamageInstance(
                    multiplier=1.452,
                    scaling_stat=StatType.ATK,
                    damage_type=DamageType.NORMAL_ATTACK,
                    element=Element.PHYSICAL,
                    tag="Gaming Normal Attack",
                    icd_interval=3)
            ]
                ),
        Talent(
            name="Stellar Rend N3",
            description="Gaming N3",
            damage_instances=[
                DamageInstance(
                    multiplier=1.959,
                    scaling_stat=StatType.ATK,
                    damage_type=DamageType.NORMAL_ATTACK,
                    element=Element.PHYSICAL,
                    tag="Gaming Normal Attack",
                    icd_interval=3)
            ]
                ),
        Talent(
            name="Stellar Rend N4",
            description="Gaming N4",
            damage_instances=[
                DamageInstance(
                    multiplier=1.38,
                    scaling_stat=StatType.ATK,
                    damage_type=DamageType.NORMAL_ATTACK,
                    element=Element.PHYSICAL,
                    tag="Gaming Normal Attack",
                    icd_interval=3)
            ]
                ),
        ]
)

bestial_ascent = Talent(
    name="Bestial Ascent",
    description="Gaming Skill",
    damage_instances=[
        DamageInstance(multiplier=3.917,
                       scaling_stat=StatType.ATK,
                       damage_type=DamageType.SKILL,
                       element=Element.QUANTUM,
                       aoe_radius=1
                       )
    ]
)

aura_app = Talent(
    name="Dendro App",
    description="Gaming Skill",
    damage_instances=[
        DamageInstance(multiplier=3.917,
                       scaling_stat=StatType.ATK,
                       damage_type=DamageType.SKILL,
                       element=Element.DENDRO,
                       aoe_radius=0.0
                       )
    ]
)

suanni_dance = Talent(
    name="Suanni's Gilded Dance",
    description="Gaming Burst",
    damage_instances=[
        DamageInstance(multiplier=6.297,
                       scaling_stat=StatType.ATK,
                       damage_type=DamageType.SKILL,
                       element=Element.ELECTRO,
                       aoe_radius=3.0
                       )
    ]
)

gaming.set_normal_attack_chain(stellar_rend)
gaming.add_talent(bestial_ascent, "skill")
gaming.add_talent(aura_app, "skill")
gaming.add_talent(suanni_dance, "burst")

#end of list
all_characters = [yanfei]