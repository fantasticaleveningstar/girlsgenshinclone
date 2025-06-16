from enum import Enum, auto
import random
import heapq
import itertools
import uuid
from dataclasses import dataclass, field
from collections import defaultdict
from typing import Optional, Callable
from core import Character, StatType, Summon, get_speed
from constants import ELEMENT_EMOJIS

class Buff:
    def __init__(self, name, description, stat=None, amount=0, duration=0, source=None, trigger="on_turn_start", reversible=False, effect=None, cleanup_effect=None):
        self.name = name
        self.description = description
        self.stat = stat  # e.g., StatType.ATK
        self.amount = amount  # e.g., +0.2 means +20%
        self.duration = duration
        self.remaining_turns = duration
        self.trigger = trigger
        self.reversible = reversible
        self.source = source  # Optional: who applied it
        self.effect = effect
        self.cleanup_effect = cleanup_effect
        self.applied = False

class BuffTimerUnit:
    def __init__(self, buff: Buff, owner, speed: int = 100):
        self.buff = buff
        self.owner = owner  # Who the buff affects
        self.name = f"{buff.name} Timer"
        self.speed = speed
        self.current_hp = 1  # Not used, just for compatibility

    def get_stat(self, stat):
        # Only SPD matters
        return self.speed

class TurnManager:
    BASE_TURN_VALUE = 10000
    
    def __init__(self, characters: list[Character]):
        self.timeline = []
        self.counter = itertools.count()
        self.time = 0
        self.buff_timers = []
        self.units = list(characters)
        self.player_team_size = len([c for c in characters if isinstance(c, Character)]) // 2

        for char in characters:
            speed = char.get_stat(StatType.SPD)
            initial_time = self.BASE_TURN_VALUE / speed
            order = next(self.counter)
            heapq.heappush(self.timeline, (initial_time, order, char))
    
    def next_turn(self):
        current_time, _, char = heapq.heappop(self.timeline)
        self.time = current_time

        if hasattr(char, "turn_shifted"):
            char.turn_shifted = False

        speed = get_speed(char)
        next_time = current_time + (self.BASE_TURN_VALUE / speed)

        order = next(self.counter)
        heapq.heappush(self.timeline, (next_time, order, char))

        return char
    
    def preview_turn_order(self, limit=10):
        seen = set()
        result = []

        for time, _, char in sorted(self.timeline):
            if isinstance(char, BuffTimerUnit):
                #result.append((f"[{char.buff.name}] (on {char.owner.name})", int(time)))
                label = f"[{char.buff.name}] (on {char.owner.name})"
            elif char not in seen:
                #result.append((char.name, int(time)))
                label = char.name
                seen.add(char)
            else:
                continue

            if hasattr(char, "current_hp") and hasattr(char, "max_hp"):
                status_emoji = get_hp_status_bar(char.current_hp, char.max_hp)
                label += f" {status_emoji} ({char.current_hp:,}/{char.max_hp:,} HP)"

            # ENERGY
            if hasattr(char, "energy_pool") and char.energy_pool:
                energy_strs = []
                for etype, val in char.energy_pool.items():
                    symbol = "🔋"  # optionally map energy types to emojis
                    name = etype.name if hasattr(etype, "name") else str(etype)
                    energy_strs.append(f"{symbol}{name}:{val}")
                label += f" | {' '.join(energy_strs)}"

            # AURAS
            if hasattr(char, "auras") and char.auras:
                aura_emojis = [ELEMENT_EMOJIS.get(aura.element, "❓") for aura in char.auras]
                label += f" | {''.join(aura_emojis)}"

            if hasattr(char, "turn_shifted") and char.turn_shifted:
                label = f"**{label}** [Moved]"
                
            result.append((label, int(time)))

        
        print("\nAction Order:")
        for i, (name, time) in enumerate(result, 1):
            print(f" {i}. {name} (in {time - self.time:.1f} AV)")

    def add_summon(self, summon: Summon):
        speed = getattr(summon, "speed", 100)
        order = next(self.counter)
        initial_time = self.time + (self.BASE_TURN_VALUE / speed)
        heapq.heappush(self.timeline, (initial_time, order, summon))
        self.units.append(summon)

    def add_buff_timer(self, buff: Buff, owner: Character, speed: int = 100):
        timer = BuffTimerUnit(buff, owner, speed)
        self.buff_timers.append(timer)
        self.units.append(timer)
        initial_time = self.time + 50 + (self.BASE_TURN_VALUE / speed)
        order = next(self.counter)
        heapq.heappush(self.timeline, (initial_time, order, timer))

    def adjust_turn(self, unit, offset: float):
        """Advance or delay a unit's next turn by `offset` AV units."""
        new_timeline = []
        adjusted = False

        for time, order, char in self.timeline:
            if char == unit and not adjusted:
                new_time = max(0, time + offset)
                new_entry = (new_time, order, char)
                new_timeline.append(new_entry)
                unit.turn_shifted = True  # ✅ mark the shift
                adjusted = True
            else:
                new_timeline.append((time, order, char))

        heapq.heapify(new_timeline)
        self.timeline = new_timeline
        print(f"{unit.name}'s action time adjusted by {offset:+.0f} AV.")
        
    def delay_by_percent(self, unit, percent: float):
        """Delay or advance a unit by a percentage of their cycle time."""
        speed = unit.get_stat(StatType.SPD)
        cycle = self.BASE_TURN_VALUE / speed
        offset = cycle * percent
        self.adjust_turn(unit, offset)

def get_hp_status_bar(current: int, maximum: int) -> str:
    if maximum == 0:
        return "❓"

    percent = current / maximum

    if percent > 0.75:
        return "🟩"
    elif percent > 0.4:
        return "🟨"
    elif percent > 0:
        return "🟥"
    else:
        return "💀"