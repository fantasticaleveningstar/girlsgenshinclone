def print_grid(units: list, field_objects: list, width: int = 10, height: int = 10):
    grid = [["." for _ in range(width)] for _ in range(height)]

    for unit in units:
        if hasattr(unit, "position") and unit.current_hp > 0:
            x, y = unit.position.x, unit.position.y
            symbol = unit.name[0].upper()
            grid[y][x] = symbol

    for obj in field_objects:
        if hasattr(obj, "position") and getattr(obj, "active", True):
            x, y = obj.position.x, obj.position.y
            grid[y][x] = "🌱"

    print("\nBattlefield Grid:")
    for row in reversed(grid):  # Reverse so y=0 is at the bottom
        print(" ".join(row))