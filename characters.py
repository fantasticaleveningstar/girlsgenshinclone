from enum import Enum, auto
import random
import heapq
import itertools
import uuid
from dataclasses import dataclass, field
from collections import defaultdict
from typing import Optional, Callable
from core import Character, StatType, Element, DamageInstance, DamageType, Talent, NormalAttackChain, Summon
from turn import TurnManager, Buff
from combat import summon_salon_members

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
                    
def shinobu_heal(attacker, _, __):
    heal_amount = int(0.15 * attacker.get_stat(StatType.HP))
    attacker.current_hp = min(attacker.max_hp, attacker.current_hp + heal_amount)
    print(f"{attacker.name} heals for {heal_amount} HP after using skill.")
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
                    tag="Yanfei Normal Attack",
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
)

def gain_fanfare_from_hp_change(observer: Character, unit: Character, old_hp: int, new_hp: int):
    if not hasattr(observer, "fanfare_points"):
        return

    max_hp = unit.max_hp
    delta = abs(new_hp - old_hp)
    percent_change = (delta / max_hp) * 100
    points_gained = int(percent_change)

    if points_gained > 0:
        observer.fanfare_points += points_gained
        print(f"{observer.name} gains {points_gained} Fanfare (total: {observer.fanfare_points}) from {unit.name}'s HP change.")

def update_party_revelry_bonuses(buff: Buff, unit: Character):
    source = buff.source
    if not hasattr(source, "fanfare_points"):
        return

    bonus_pct = source.fanfare_points * 0.0023  # Example: +0.03% per point
    healing_bonus = source.fanfare_points * 0.0009  # Example: +0.04% per point
    unit.general_dmg_bonus += bonus_pct
    print(f"{unit.name} receives {bonus_pct*100:.1f}% DMG bonus from Universal Revelry.")

def apply_universal_revelry(attacker: Character, defender: Character, turn_manager: TurnManager):
    attacker.fanfare_points = 0  # start from 0
    duration = 3

    for ally in turn_manager.units:
        if isinstance(ally, Character):
            buff = Buff(
                name="Universal Revelry",
                description="Scales party DMG and healing based on Furina’s Fanfare.",
                duration=duration,
                trigger="on_turn_start",  # will be refreshed per turn
                source=attacker,
                reversible=True,
                effect=update_party_revelry_bonuses,
                cleanup_effect=lambda char: setattr(attacker, "fanfare_points", 0)
            )
            ally.buffs.append(buff)
            turn_manager.add_buff_timer(buff, ally)
            print(f"{ally.name} is empowered by Universal Revelry.")

    return 0, []

furina.set_normal_attack_chain(soloists_solicitation)
furina.add_talent(salon_solitaire, "skill")
furina.add_talent(people_rejoice, "burst")

#end of list
all_characters = [yanfei]