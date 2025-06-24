from core import *

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
