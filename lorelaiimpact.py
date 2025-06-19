from enum import Enum, auto
import random
import heapq
import itertools
import uuid
from dataclasses import dataclass, field
from collections import defaultdict
from typing import Optional, Callable
from core import Character, Element, StatType, Talent, DamageInstance, DamageType, Summon, Passive, NormalAttackChain, Position, place_in_grid
from combat import calculate_damage, apply_icd, salon_attack_action, summon_salon_members, notify_hp_change, take_damage, heal, notify_damage_taken, resolve_reactions, trigger_event, log_damage, log_heal, get_living_allies, get_targets_in_radius
from turn import TurnManager, Buff, BuffTimerUnit
from characters import gaming

CAN_DOUBLE_AURA = {Element.HYDRO, Element.PYRO, Element.CRYO, Element.ELECTRO}

coexistence_rules = {
    Element.HYDRO: [Element.PYRO],
    Element.PYRO: [Element.HYDRO, Element.CRYO],
    Element.CRYO: [Element.PYRO],
    "Quicken": [Element.DENDRO, Element.ELECTRO],
    Element.DENDRO: ["Quicken"],
    Element.ELECTRO: ["Quicken"],
    }

player_team = []

def grant_energy(regular=0, special_type=None, special_amount=0):
    def effect(attacker, *args, **kwargs):
        if regular > 0:
            attacker.energy_pool["Elemental Energy"] = attacker.energy_pool.get("Elemental Energy", 0) + regular
            print(f"{attacker.name} gains {regular} Energy.")
        if special_type and special_amount > 0:
            attacker.energy_pool[special_type] = attacker.energy_pool.get(special_type, 0) + special_amount
            print(f"{attacker.name} gains {special_amount} {special_type}.")
    return effect

def apply_buff_trigger(character: Character, event: str):
    for buff in character.buffs:
        if buff.trigger == event:
            if buff.effect:
                buff.effect(buff=buff, unit=character)
            elif buff.stat:  # fallback to stat buffs
                bonus = character.base_stats[buff.stat] * buff.amount
                character.stats[buff.stat] += bonus
                print(f"{character.name}'s {buff.stat.name} increased by {bonus} from {buff.name}.")
            buff.applied = True

def cleanup_expired_buffs(character: Character):
    active_buffs = []
    for buff in character.buffs:
        if buff.remaining_turns <= 1:
            if buff.reversible:
                if buff.cleanup_effect:
                    buff.cleanup_effect(character)
                elif buff.stat:
                    reduction = character.base_stats[buff.stat] * buff.amount
                    character.stats[buff.stat] -= reduction
                    print(f"{character.name}'s {buff.stat.name} returned to normal.")
            print(f"{buff.name} expired on {character.name}.")
        else:
            buff.remaining_turns -= 1
            active_buffs.append(buff)
    character.buffs = active_buffs

def apply_buff(character: Character, buff: Buff):
    if not buff.applied:
        if buff.stat is not None:
            original = character.stats.get(buff.stat, 0)
            bonus = character.base_stats[buff.stat] * buff.amount
            character.stats[buff.stat] = original + bonus
            print(f"{character.name} gains {buff.name}: {buff.description}")
        elif buff.effect:  # purely functional buff
            buff.effect(character)
        buff.applied = True
    character.buffs.append(buff)

def entropic_bind(attacker, defender, turn_manager):
    delay_amount = 0.25  # you can make this scale with SPD, DEF, etc.
    print(f"{attacker.name} uses Entropic Bind! Delaying {defender.name}'s next turn by {delay_amount * 100}%.")
    turn_manager.delay_by_percent(defender, delay_amount)

    return 0, []

def action_advance(attacker, defender, turn_manager):
    advance_amount = -1  # you can make this scale with SPD, DEF, etc.
    print(f"{attacker.name} advances their action by {advance_amount * 100}%.")
    turn_manager.delay_by_percent(attacker, advance_amount)

    return 0, []

def use_normal_attack(attacker: Character, defender: Character, turn_manager: TurnManager, summary: dict = None, taken_summary: dict = None):
    attacks = attacker.get_active_normal_chain()
    if not attacks:
        print(f"{attacker.name} has no normal attacks.")
        return 0, [], False

    index = attacker.combo_index
    talent = attacks.get_talent(index)

    print(f"{attacker.name} uses {attacks.name} ({talent.name})!")

    total_damage = 0
    all_reactions = []

    for instance in talent.damage_instances:
        allow_element = apply_icd(attacker, defender, instance)
        effective_element = instance.element if allow_element else None

        modified_instance = DamageInstance(
            multiplier=instance.multiplier,
            scaling_stat=instance.scaling_stat,
            damage_type=instance.damage_type,
            description=instance.description,
            element=effective_element,
            icd_tag=instance.icd_tag,
            icd_interval=instance.icd_interval,
            base_dmg_multiplier=instance.base_dmg_multiplier,
            additive_base_dmg_bonus=instance.additive_base_dmg_bonus,
        )

        result = calculate_damage(attacker, defender, modified_instance, turn_manager)

        damage = result["damage"]
        total_damage += damage
        all_reactions.extend(result["reactions"])
        actual = take_damage(defender, damage, source=attacker, team=[defender],
                     summary=summary, taken_summary=taken_summary)
        
        log_damage(
            source=attacker,
            target=defender,
            amount=actual,
            element=result["element"],
            crit=result["crit"],
            label=result["label"],
            applied_element=result.get("applied_element", False)
        )

    # Handle any on-use effects (list-based)
    if talent.on_use:
        for effect_fn in talent.on_use:
            effect_fn(attacker, defender, turn_manager)

    # Advance combo index
    attacker.combo_index += 1
    combo_complete = attacker.combo_index >= attacks.length()

    return total_damage, all_reactions, combo_complete

def use_skill(attacker: Character, defender: Character, skill_index=0):
    reset_combo(attacker)  # Reset combo
    skill = attacker.skills[skill_index]
    return use_talent(attacker, defender, skill)

def use_burst(attacker: Character, defender: Character, burst_index=0):
    reset_combo(attacker)  # Reset combo
    burst = attacker.bursts[burst_index]
    return use_talent(attacker, defender, burst)

def choose_action(character: Character):
    print(f"\n Choose an action:")

    options = []
    index = 1

    chain = character.get_active_normal_chain()
    if chain:
        next_index = character.combo_index % len(chain.talents)
        next_talent = chain.get_talent(next_index)
        print(f"{index}. Normal Attack: {chain.name} - {next_talent.name}")
        options.append(("normal", None))
        index += 1


    for talent in character.skills:
        if talent.form_lock and character.current_form != talent.form_lock:
            continue
        cd = character.cooldowns.get(talent.id, 0)
        energy = character.energy_pool.get(talent.energy_type, 0)
        cost = talent.energy_cost
        energy_status = ""
        if energy < cost:
            energy_status = "(Insufficient Energy)"
        cooldown_text = f"(CD: {cd})" if cd > 0 else ""
        cost_text = f"(Cost: {talent.energy_cost} {talent.energy_type})" if talent.energy_cost > 0 else ""
        print(f"{index}. Skill: {talent.name} {cooldown_text} {cost_text} {energy_status}")
        options.append(("skill", talent))
        index += 1
    
    for talent in character.bursts:
        if talent.form_lock and character.current_form != talent.form_lock:
            continue
        cd = character.cooldowns.get(talent.id, 0)
        energy = character.energy_pool.get(talent.energy_type, 0)
        cost = talent.energy_cost
        energy_status = ""
        if energy < cost:
            energy_status = "(Insufficient Energy)"
        cooldown_text = f"(CD: {cd})" if cd > 0 else ""
        cost_text = f"(Cost: {talent.energy_cost} {talent.energy_type})" if talent.energy_cost > 0 else ""
        print(f"{index}. Burst: {talent.name} {cooldown_text} {cost_text} {energy_status}")
        options.append(("burst", talent))
        index += 1
    
    print(f"{index}. End Turn")
    options.append(("end", None))

    while True:
        try:
            choice = int(input("> "))
            if 1 <= choice <= len(options):
                return options[choice - 1]
        except ValueError:
            pass
        print("Invalid options. Try again.")

def reset_combo(character):
    character.combo_index = 0

dummy_a = Character(
    "Dummy A",
    base_stats={StatType.HP: 5000000, StatType.ATK: 10, StatType.SPD: 10},
    element=Element.PYRO
)

dummy_b = Character(
    "Dummy B",
    base_stats={StatType.HP: 5000000, StatType.ATK: 10, StatType.SPD: 10},
    element=Element.PYRO
)

dummy_c = Character(
    "Dummy C",
    base_stats={StatType.HP: 5000000, StatType.ATK: 10, StatType.SPD: 10},
    element=Element.PYRO
)


dummy_a.position = Position(x=0, y=0)
dummy_b.position = Position(x=1, y=1)
dummy_c.position = Position(x=4, y=1)

dummy_a.apply_elemental_effect(Element.ELECTRO)

dummies = [dummy_a, dummy_b, dummy_c]
place_in_grid(dummies, columns=3)


def battle_loop(player_team: list[Character], enemy_team: list[Character]):
    for unit in player_team:
        unit.team = player_team
    for unit in enemy_team:
        unit.team = enemy_team

    all_characters = player_team + enemy_team
    turn_manager = TurnManager(all_characters)
    turn_manager.player_team_size = len(player_team)


    def is_alive(character):
        return character.current_hp > 0
    
    def get_living(team):
        return [char for char in team if is_alive(char)]
    
    while get_living(player_team) and get_living(enemy_team):
        turn_damage_summary = defaultdict(int)
        turn_damage_taken = defaultdict(int)
        turn_manager.preview_turn_order()

        current_char = turn_manager.next_turn()
        trigger_event("on_turn_start", [current_char], unit=current_char)

        if isinstance(current_char, BuffTimerUnit):
            buff = current_char.buff

            # Apply effect if needed
            buff.applied = True


            buff.remaining_turns -= 1
            print(f"[DEBUG] {buff.name} timer ticking on {current_char.owner.name} — {buff.remaining_turns} turns left")
            print(f"[DEBUG] Active buffs on {current_char.owner.name}: {[b.name for b in current_char.owner.buffs]}")
            
            if buff.remaining_turns <= 0:
                print(f"[Countdown] {buff.name} ticked. (0 turns remaining)")
                print(f"[Countdown] {buff.name} has expired.")
                if buff.cleanup_effect:
                    buff.cleanup_effect(current_char.owner)
                current_char.owner.buffs = [
                b for b in current_char.owner.buffs
                if not (b.name == buff.name and b.source == buff.source)
            ]


                # Remove timer unit
                turn_manager.units.remove(current_char)
                turn_manager.buff_timers.remove(current_char)
                turn_manager.timeline = [
                    (t, o, c) for (t, o, c) in turn_manager.timeline if c != current_char
                ]
                heapq.heapify(turn_manager.timeline)
            else:
                print(f"[Countdown] {buff.name} ticked. ({buff.remaining_turns} turns remaining)")                
            continue


        if not is_alive(current_char):
            continue

        trigger_event("on_turn_start", [current_char], unit=current_char)

        print(f"\n=========={current_char.name}'s Turn==========")

        if isinstance(current_char, Summon):
            if current_char.frozen:
                print(f"{current_char.name} is frozen and cannot act!")
                current_char.frozen = False
                continue

            current_char.handle_event("on_turn_start")
            current_char.handle_event("on_action", enemy_team=get_living(enemy_team if current_char.owner in player_team else player_team))
            current_char.handle_event("on_turn_end")

            # Check for expiration by duration
            if current_char.duration is not None:
                current_char.remaining_duration -= 1
                if current_char.remaining_duration <= 0:
                    print(f"{current_char.name} has expired (duration ended).")
                    if current_char in current_char.owner.summons:
                        current_char.owner.summons.remove(current_char)
                    if current_char in turn_manager.units:
                        turn_manager.units.remove(current_char)
                    turn_manager.timeline = [(t, o, c) for (t, o, c) in turn_manager.timeline if c != current_char]
                    heapq.heapify(turn_manager.timeline)
                    continue

            # Check for expiration by death
            if current_char.current_hp <= 0:
                print(f"{current_char.name} has expired (defeated).")
                if current_char in current_char.owner.summons:
                    current_char.owner.summons.remove(current_char)
                if current_char in turn_manager.units:
                    turn_manager.units.remove(current_char)
                turn_manager.timeline = [(t, o, c) for (t, o, c) in turn_manager.timeline if c != current_char]
                heapq.heapify(turn_manager.timeline)
                continue
            continue

        if current_char.energy_pool:
            energy_status = ', '.join(f"{etype.name if isinstance(etype, Enum) else etype}: {amount}" 
                              for etype, amount in current_char.energy_pool.items())
            print(f"Energy → {energy_status}")
        else:
            print(f"Energy → None")
        
        

        if current_char in player_team:
            combo_active = True
            while combo_active:
                action_type, action = choose_action(current_char)

                if action_type == "pass":
                    reset_combo(current_char) # Reset combo string
                    print(f"{current_char.name} ends their turn.")

                if action_type == "end":
                    print(f"{current_char.name} ends their turn.")
                    reset_combo(current_char)
                    break

                living_enemies = get_living(enemy_team)
                if not living_enemies:
                    break
                target = living_enemies[0]

                if action_type == "normal":
                    damage, reactions, na_string_done = use_normal_attack(current_char, target, turn_manager)
                    take_damage(target, damage, source=current_char, team=player_team)

                    resolve_reactions(reactions, player_team)
                
                    if na_string_done:
                        print(f"{current_char.name}'s combo string is complete.")
                        reset_combo(current_char)
                        combo_active = False
                    else:
                        continue_prompt = input("\nContinue attacking? (y/n): ").strip().lower()
                        if continue_prompt != "y":
                            reset_combo(current_char)
                            combo_active = False

                else:
                    damage, reactions = use_talent(current_char, target, action, turn_manager, summary=turn_damage_summary, taken_summary=turn_damage_taken)
                    take_damage(target, damage, source=current_char, team=player_team)

                    resolve_reactions(reactions, player_team)

                    reset_combo(current_char)  # Break combo
                    combo_active = False
            trigger_event("on_turn_end", [current_char], unit=current_char)
            cleanup_expired_buffs(current_char)
            

            for tid in list(current_char.cooldowns):
                current_char.cooldowns[tid] -= 1
                if current_char.cooldowns[tid] <= 0:
                    del current_char.cooldowns[tid]

        #enemy turn
        else:
            living_targets = get_living(player_team)
            if not living_targets:
                break
            target = random.choice(living_targets)

            if current_char.skills:
                move = current_char.skills[0]
                print(f"{current_char.name} targets {target.name}!")
                damage, reactions = use_talent(current_char, target, move, turn_manager)
                take_damage(target, damage, source=current_char, team=player_team)
                print(f"[DEBUG] Final reactions to resolve: {reactions}")
                for r in reactions:
                    resolve_reactions([r], [r.target])
            else:
                print(f"{current_char.name} has no skills to use and skips their turn.")
        current_char.decay_auras()

        if turn_damage_summary:
            print("\n📊 Damage Dealt This Turn:")
            for name, dmg in turn_damage_summary.items():
                print(f"  - {name}: {dmg:,} DMG")

        if turn_damage_taken:
            print("\n🩸 Damage Taken This Turn:")
            for name, dmg in turn_damage_taken.items():
                print(f"  - {name}: {dmg:,} DMG")


    if get_living(player_team):
        print("\n🏆 Victory! Your team wins.")
    else:
        print("\n💀 Defeat. Your team has been wiped out.")

def use_talent(attacker: Character, defender: Character, talent: Talent, turn_manager: TurnManager, summary: dict = None, taken_summary: dict = None):
    all_enemies = [unit for unit in turn_manager.units if unit.team != attacker.team]
    energy_type = talent.energy_type
    energy_cost = talent.energy_cost

    # === ENERGY CHECK ===
    if energy_type and attacker.energy_pool.get(energy_type, 0) < energy_cost:
        print(f"⚠️ {attacker.name} lacks {energy_type} energy to use {talent.name}.")
        return 0, []

    # === COOLDOWN CHECK ===
    if attacker.cooldowns.get(talent.id, 0) > 0:
        print(f"⏳ {talent.name} is on cooldown for {attacker.cooldowns[talent.id]} more turn(s).")
        return 0, []

    # Apply cooldown
    if talent.cooldown > 0:
        attacker.cooldowns[talent.id] = talent.cooldown + 1

    print(f"\n🔷 {attacker.name} uses **{talent.name}**!")

    total_damage = 0
    all_reactions = []

    for instance in talent.damage_instances:
        allow_element = apply_icd(attacker, defender, instance)
        effective_element = instance.element if allow_element else None

        # Construct modified instance (non-destructive to talent base)
        modified_instance = DamageInstance(
            multiplier=instance.multiplier,
            scaling_stat=instance.scaling_stat,
            damage_type=instance.damage_type,
            description=instance.description,
            element=effective_element,
            icd_tag=instance.icd_tag,
            icd_interval=instance.icd_interval,
            aoe_radius=instance.aoe_radius
        )

        if modified_instance.aoe_radius > 0:
            targets = get_targets_in_radius(defender, all_enemies, modified_instance.aoe_radius)
            targets.insert(0, defender)  # include primary target
        else:
            targets = [defender]

        for target in targets:
            result = calculate_damage(attacker, target, modified_instance, turn_manager)
            damage = result["damage"]
            all_reactions.extend(result["reactions"])

            actual = take_damage(
                target,
                damage,
                source=attacker,
                team=[target],
                summary=summary,
                taken_summary=taken_summary
            )

            log_damage(
                source=attacker,
                target=target,
                amount=actual,
                element=result["element"],
                crit=result["crit"],
                label=result["label"],
                applied_element=result.get("applied_element", False)
            )

    allies = get_living_allies(attacker, turn_manager)

    # === ON-USE EFFECTS (Buffs, healing, summons, etc.) ===
    for effect_fn in talent.on_use:
        if callable(effect_fn):
            result = effect_fn(attacker, defender, turn_manager, team=allies)
            if isinstance(result, tuple) and len(result) == 2:
                extra_damage, extra_reactions = result
                total_damage += extra_damage
                all_reactions.extend(extra_reactions)

    # === ENERGY COST ===
    if energy_cost > 0:
        attacker.energy_pool[energy_type] -= energy_cost

    return total_damage, all_reactions



battle_loop(player_team=[gaming], enemy_team=[dummy_a, dummy_b, dummy_c])
