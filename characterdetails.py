"""#Normal Attack
lucent_moonglow = Talent(
    name="Lucent Moonglow",
    damage_multiplier=0.5,
    scaling_stat=StatType.HP,
    damage_type=DamageType.NORMAL_ATTACK,
    element=Element.CRYO,
    description="Deals minor Cryo DMG equal to X% of Jingliu's Max HP."
)

missed_catch = Talent(
    name="Oops, a Missed Catch",
    damage_multiplier=0.5,
    scaling_stat=StatType.ATK,
    damage_type=DamageType.NORMAL_ATTACK,
    element=Element.QUANTUM,
    description="Deals Quantum DMG equal to 50% of Cipher's ATK."
)

dimmed_star = NormalAttackChain(
    name="Dimmed Star's Light",
    talents=[
        Talent("Dimmed Star's Light N1", 0.7293, StatType.ATK, DamageType.NORMAL_ATTACK, Element.PHYSICAL),
        Talent("Dimmed Star's Light N2", 0.7072, StatType.ATK, DamageType.NORMAL_ATTACK, Element.PHYSICAL),
        Talent("Dimmed Star's Light N3", 1.0453, StatType.ATK, DamageType.NORMAL_ATTACK, Element.PHYSICAL),
    ]
)

weaving_blade = NormalAttackChain(
    name="Weaving Blade",
    talents=[
        Talent("Weaving Blade N1", 0.977, StatType.ATK, DamageType.NORMAL_ATTACK, Element.PHYSICAL),
        Talent("Weaving Blade N2", 0.926, StatType.ATK, DamageType.NORMAL_ATTACK, Element.PHYSICAL),
        Talent("Weaving Blade N3", 1.202, StatType.ATK, DamageType.NORMAL_ATTACK, Element.PHYSICAL),
        Talent("Weaving Blade N4", 1.485, StatType.ATK, DamageType.NORMAL_ATTACK, Element.PHYSICAL),
    ]
)
#Elemental Skill
transcendent_flash = Talent(
    name="Transcendent Flash",
    damage_multiplier=1.5,
    scaling_stat=StatType.HP,
    damage_type=DamageType.SKILL,
    element=Element.CRYO,
    description="Deals Cryo DMG equal to X% of Jingliu's Max HP.",
    on_use=entropic_bind
)

tamoto_talents = [
    Talent(
        name="Static Zap",
        damage_multiplier=0.75,
        scaling_stat=StatType.DEF,
        damage_type=DamageType.SKILL,
        element=Element.ELECTRO,
        description="Zaps the closest enemy."
    ),
    Talent(
        name="Charged Discharge",
        damage_multiplier=1.2,
        scaling_stat=StatType.DEF,
        damage_type=DamageType.SKILL,
        element=Element.ELECTRO,
        description="A stronger attack every other turn."
    )
]


jackpot_taking = Talent(
    name="Hey, Jackpot for the Taking",
    damage_multiplier=1,
    scaling_stat=StatType.ATK,
    damage_type=DamageType.SKILL,
    element=Element.QUANTUM,
    description="Deals Quantum DMG equal to 100% of Cipher's ATK."
)

radiant_dreams = Talent(
    name="Radiant Dreams",
    damage_multiplier=1.2096,
    scaling_stat=StatType.ATK,
    damage_type=DamageType.SKILL,
    element=Element.CRYO,
    description="Cordelia enters Nightsoul's Blessing.",
    on_use=activate_nightsoul,
    cooldown=3,
)

fluttering_hasode = Talent(
    name="Fluttering Hasode",
    damage_multiplier=1.85,
    scaling_stat=StatType.DEF,
    damage_type=DamageType.SKILL,
    element=Element.GEO,
    description="Summons Tamoto.",
)

fluttering_hasode.on_use = lambda attacker, defender, turn_manager: summon_tamoto(attacker, defender, turn_manager)


bestial_ascent = Talent(
    name="Bestial Ascent",
    damage_multiplier=1.85,
    scaling_stat=StatType.DEF,
    damage_type=DamageType.SKILL,
    element=Element.PYRO,
    description="Gaming skill.",
    on_use=grant_energy(regular=10)
)

white_clouds = Talent(
    name="White Clouds at Dawn",
    damage_multiplier=1.85,
    scaling_stat=StatType.DEF,
    damage_type=DamageType.SKILL,
    element=Element.ANEMO,
    description="Xianyun skill.",
    on_use=the_finishing_touch,
)

floral_brush = Talent(
    name="Floral Brush",
    damage_multiplier=1.85,
    scaling_stat=StatType.DEF,
    damage_type=DamageType.SKILL,
    element=Element.DENDRO,
    description="Collei skill.",
    on_use=grant_energy(regular=10)
)

salon_solitaire = Talent(
    name="Salon Solitaire",
    damage_multiplier=1.85,
    scaling_stat=StatType.DEF,
    damage_type=DamageType.SKILL,
    element=Element.HYDRO,
    description="Furina skill.",
    on_use=grant_energy(regular=10)
)

ceremonial_crystalshot = Talent(
    name="Ceremonial Crystalshot",
    damage_multiplier=1.85,
    scaling_stat=StatType.DEF,
    damage_type=DamageType.SKILL,
    element=Element.GEO,
    description="Navia skill.",
    on_use=grant_energy(regular=10)
)

dawnfrost_darkstar = Talent(
    name="Dawnfrost Darkstar",
    damage_multiplier=1.85,
    scaling_stat=StatType.DEF,
    damage_type=DamageType.SKILL,
    element=Element.CRYO,
    description="Citlali skill.",
    on_use=grant_energy(regular=10)
)




#Burst
florephemeral_dreamflux = Talent(
    name="Florephemeral Dreamflux",
    damage_multiplier=4.5,
    scaling_stat=StatType.HP,
    damage_type=DamageType.BURST,
    element=Element.CRYO,
    description="Deals massive Cryo DMG equal to X% of Jingliu's Max HP."
)

kitty_phantom = Talent(
    name="Yours Truly, Kitty Phantom Thief!",
    damage_multiplier=1.5,
    scaling_stat=StatType.ATK,
    damage_type=DamageType.BURST,
    element=Element.QUANTUM,
    description="Deals Quantum DMG equal to 150% of Cipher's ATK.",
    energy_type="coins",
    energy_cost=9,
    cooldown=3
)

midnight_starfall = Talent(
    name="Midnight Starfall",
    damage_multiplier=4.1778,
    scaling_stat=StatType.ATK,
    damage_type=DamageType.BURST,
    element=Element.CRYO,
    description="Cordelia deals Nightsoul-aligned DMG.",
    energy_type="Elemental Energy",
    energy_cost=50,
    cooldown=3
)

frosted_starpiercer = Talent(
    name="Frosted Starpiercer",
    damage_multiplier=4.6926,
    scaling_stat=StatType.ATK,
    damage_type=DamageType.NORMAL_ATTACK,
    element=Element.CRYO,
    description="Cordelia deals Nightsoul-aligned Plunging DMG.",
    energy_type="Nightsoul",
    energy_cost=30,
    on_use=lambda attacker, _: apply_buff(attacker, cordelia_nightsoul)
)

shatterlight_strikes = NormalAttackChain(
    name="Shatterlight Strikes",
    talents=[
        Talent("Shatterlight Strike N1", 1.5948, StatType.ATK, DamageType.NORMAL_ATTACK, Element.CRYO, on_use=grant_energy(special_type="Nightsoul", special_amount=10)),
        Talent("Shatterlight Strike N2", 1.6992, StatType.ATK, DamageType.NORMAL_ATTACK, Element.CRYO, on_use=grant_energy(special_type="Nightsoul", special_amount=10)),
        Talent("Shatterlight Strike N3", 1.9008, StatType.ATK, DamageType.NORMAL_ATTACK, Element.CRYO, on_use=grant_energy(special_type="Nightsoul", special_amount=10)),
    ]
)

hiyoku_twin_blades = Talent(
    name="Hiyoku: Twin Blades",
    damage_multiplier=5.77,
    scaling_stat=StatType.DEF,
    damage_type=DamageType.BURST,
    element=Element.ELECTRO,
    description="Chiori Burst.",
    energy_type="Elemental Energy",
    energy_cost=50,
    cooldown=2
)"""

"""jingliu.add_talent(lucent_moonglow, "normal")
jingliu.add_talent(transcendent_flash, "skill")
jingliu.add_talent(spectral_transmigration, "skill")
jingliu.add_talent(florephemeral_dreamflux, "burst")



cipher.add_talent(missed_catch, "normal")
cipher.add_talent(jackpot_taking, "skill")
cipher.add_talent(kitty_phantom, "burst")

cordelia.set_normal_attack_chain(dimmed_star)
cordelia.set_form_locked_chain("Nightsoul", shatterlight_strikes)
cordelia.add_talent(radiant_dreams, "skill")
cordelia.add_talent(midnight_starfall, "burst")
cordelia.add_talent(frosted_starpiercer, "skill")

chiori.set_normal_attack_chain(weaving_blade)
chiori.add_talent(fluttering_hasode, "skill")
chiori.add_talent(hiyoku_twin_blades, "burst")

radiant_dreams.form_lock = None  # Only when NOT in Nightsoul
frosted_starpiercer.form_lock = "Nightsoul"""

"""def create_tamoto(owner):
    def on_turn_start(self, **kwargs):
        print(f"{self.name} begins charging...")

    def on_action(self, **kwargs):
        enemy_team = kwargs.get("enemy_team", [])
        if not enemy_team:
            print(f"{self.name} finds no targets.")
            return

        if not self.talents:
            print(f"{self.name} has no talents to use.")
            return

        talent = random.choice(self.talents)  # ✅ Use random talent

        target = enemy_team[0]  # You can make this random too if you like
        print(f"{self.name} uses {talent.name} on {target.name}!")

        damage, reactions = calculate_damage(
            attacker=self,
            defender=target,
            base_multiplier=talent.damage_multiplier,
            damage_type=talent.damage_type,
            damage_element=talent.element,
            scaling_stat=talent.scaling_stat
        )
        target.current_hp = max(target.current_hp - damage, 0)
        print(f"{target.name}'s HP: {target.current_hp}/{target.max_hp}")

        for r in reactions:
            r.resolve()
            r.target.current_hp = max(r.target.current_hp - r.damage, 0)
            print(f"{r.target.name}'s HP: {r.target.current_hp}/{r.target.max_hp}")

    return Summon(
        name="Tamoto",
        owner=owner,
        stats={StatType.DEF: 200, StatType.SPD: 90},
        hp=1,
        triggers={"on_turn_start": on_turn_start, "on_action": on_action},
        duration=3,
        talents=tamoto_talents
    )



def summon_tamoto(attacker, _, turn_manager):
    tamoto = create_tamoto(attacker)
    print(f"{attacker.name} summons {tamoto.name}!")
    attacker.summons.append(tamoto)
    turn_manager.add_summon(tamoto)"""

"""def skill_boost_effect(attacker, talent, base_damage):
    if talent.damage_type == DamageType.SKILL:
        print(f"Passive Triggered: Nightsoul Burst!")
        return base_damage * 1.2
    return base_damage

skill_boost = Passive(
    name="Frosted Soul",
    description="Increases Skill damage by 20%.",
    trigger="on_calculate_damage",
    effect=skill_boost_effect
)

cordelia.add_passive(skill_boost)
cordelia_nightsoul.source = cordelia"""

"""cipher = Character("Cipher", 
                  base_stats={
                      StatType.ATK: 800,
                      StatType.DEF: 1200,
                      StatType.HP: 1200,
                      StatType.SPD: 120,
                      StatType.CRIT_RATE: 0.8,
                      StatType.CRIT_DMG: 1.6,
                      StatType.EM: 0,
                      StatType.ENERGY_RECHARGE: 1.0,
                  }, element=Element.QUANTUM)

jingliu = Character("Jingliu",
                    base_stats={
                        StatType.ATK: 600,
                        StatType.DEF: 600,
                        StatType.HP: 1650,
                        StatType.SPD: 130,
                        StatType.CRIT_RATE: 0.9,
                        StatType.CRIT_DMG: 2.2,
                        StatType.EM: 0,
                        StatType.ENERGY_RECHARGE: 1.0,
                    }, element=Element.CRYO)

cordelia = Character("Cordelia",
                     base_stats={
                        StatType.ATK: 1467,
                        StatType.DEF: 800,
                        StatType.HP: 15444,
                        StatType.SPD: 160,
                        StatType.CRIT_RATE: 0.87,
                        StatType.CRIT_DMG: 3.6,
                        StatType.EM: 0,
                        StatType.ENERGY_RECHARGE: 1.0,

                     }, element=Element.CRYO)

chiori = Character("Chiori",
                   base_stats={
                       StatType.ATK: 1438,
                       StatType.DEF: 2234,
                       StatType.HP: 19527,
                       StatType.SPD: 90,
                       StatType.CRIT_RATE: 0.803,
                       StatType.CRIT_DMG: 2.268,
                       StatType.EM: 300,
                       StatType.ENERGY_RECHARGE: 1.0,

                       }, element=Element.ELECTRO)"""

"""def activate_nightsoul(attacker, _):
    apply_buff(attacker, cordelia_nightsoul)
"""

"""def activate_spectral_transmigration(attacker, _, turn_manager):
    def end_form(owner):
        print(f"{owner.name}'s Spectral Transmigration ends. She returns to her normal form.")
        owner.current_form = None

    spectral_timer = Buff(
        name="Spectral Transmigration",
        description="Jingliu enters a spectral form for 3 global turns.",
        duration=3,
        cleanup_effect=end_form
    )

    attacker.current_form = "Spectral"
    attacker.buffs.append(spectral_timer)
    turn_manager.add_buff_timer(spectral_timer, attacker, speed=40)  # Adjust SPD if desired
    print(f"{attacker.name} enters her Spectral Transmigration form.")

##spectral_transmigration = Talent(
##    name="Spectral Transmigration",
##    damage_multiplier=0,
##    scaling_stat=StatType.ATK,
##    damage_type=DamageType.SKILL,
##    description="Enter Spectral form for 3 global turns.",
##    on_use=[activate_spectral_transmigration, action_advance],
##    cooldown=5  # Optional
##)

cordelia_nightsoul = Buff(
    name="Nightsoul's Blessing: Cordelia",
    description="Cordelia enters Nightsoul's Blessing",
    duration=3,
    trigger="on_turn_end",
    reversible=True,
    effect=enter_cordelia_nightsoul_form,
    cleanup_effect=exit_cordelia_nightsoul_form,
)
"""

"""def the_finishing_touch(attacker, buff):
    def_buff = Buff(
        name="The Finishing Touch",
        description="+30% DEF for 3 turns",
        stat=StatType.DEF,
        amount=0.3,
        duration=3,
        trigger="on_turn_start",
        reversible=True,
    )
    apply_buff(attacker, def_buff)

def enter_cordelia_nightsoul_form(character):
    character.current_form = "Nightsoul"
    cordelia.normal_attack_chain = shatterlight_strikes
    print(f"{character.name} enters the Nightsoul's Blessing state.")
    cordelia.combo_index = 0

def exit_cordelia_nightsoul_form(character):
    character.current_form = None
    cordelia.normal_attack_chain = dimmed_star
    print(f"{character.name}'s Nightsoul's Blessing has ended.")
    cordelia.combo_index = 0
"""
"""slime_attack = Talent(
    name="Slime Attack",
    damage_multiplier=0.01,
    scaling_stat=StatType.ATK,
    damage_type=DamageType.SKILL,
    element=Element.HYDRO,
    description="Fuck you"
)

dummy_attack = Talent(
    name="Dummy Attack",
    damage_multiplier=1,
    scaling_stat=StatType.ATK,
    damage_type=DamageType.SKILL,
    element=Element.PHYSICAL,
    description="Fuck you"
)"""

"""slime.add_talent(slime_attack, "skill")
dummy.add_talent(dummy_attack, "skill")"""

"""slime = Character("Churl", 
                  base_stats={StatType.HP: 5000000, StatType.SPD: 75}, 
                  element=Element.HYDRO)"""