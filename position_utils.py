from core import *
from turn import TurnManager

def distance(a: Character, b: Character) -> float:
    dx = a.position.x - b.position.x
    dy = a.position.y - b.position.y
    return (dx ** 2 + dy ** 2) ** 0.5  # Euclidean distance

def place_in_grid(units: list[Character], columns: int = 3, spacing: int = 1, start_x: int = 0, start_y: int = 0):
    for i, unit in enumerate(units):
        x = start_x + (i % columns) * spacing
        y = start_y + (i // columns) * spacing
        unit.position = Position(x=x, y=y)

def get_targets_in_radius(center: Character, candidates: list[Character], radius: float) -> list[Character]:
    return [unit for unit in candidates if unit != center and distance(center, unit) <= radius]

def get_allies(attacker: Character, turn_manager: TurnManager) -> list[Character]:
    return [
        unit for unit in turn_manager.units
        if isinstance(unit, Character)
        and is_same_team(attacker, unit, turn_manager)
    ]

def get_enemies(attacker: Character, turn_manager: TurnManager) -> list[Character]:
    return [
        unit for unit in turn_manager.units
        if isinstance(unit, Character)
        and not is_same_team(attacker, unit, turn_manager)
    ]

def is_same_team(char1: Character, char2: Character, turn_manager: TurnManager) -> bool:
    chars = [u for u in turn_manager.units if isinstance(u, Character)]
    cutoff = getattr(turn_manager, "player_team_size", len(chars) // 2)

    try:
        idx1 = chars.index(char1)
        idx2 = chars.index(char2)
    except ValueError:
        return False  # One or both chars no longer in list

    return (idx1 < cutoff and idx2 < cutoff) or (idx1 >= cutoff and idx2 >= cutoff)

def get_teams(turn_manager):
    """Splits characters into two teams using stored player_team_size."""
    chars = [u for u in turn_manager.units if isinstance(u, Character)]
    size = getattr(turn_manager, "player_team_size", len(chars) // 2)
    return chars[:size], chars[size:]

def get_living_allies(attacker: Character, turn_manager: TurnManager) -> list[Character]:
    return [
        ally for ally in get_allies(attacker, turn_manager)
        if isinstance(ally, Character) and ally.current_hp > 0
    ]

def get_living_enemies(attacker: Character, turn_manager: TurnManager) -> list[Character]:
    return [
        enemy for enemy in get_enemies(attacker, turn_manager)
        if isinstance(enemy, Character) and enemy.current_hp > 0
    ]
