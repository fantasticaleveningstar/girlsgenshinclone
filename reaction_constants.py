def is_transformative(reaction: str) -> bool:
    return reaction in {
        "Overload", "Electro-Charged", "Superconduct",
        "Pyro Swirl", "Hydro Swirl", "Electro Swirl", "Cryo Swirl","Bloom", "Hyperbloom", "Burgeon", "Burning", "Stasis", "Ignition", "Impulse", "Anchor", "Superposition",
        }

def is_amplifying(reaction: str) -> bool:
    return reaction in {
        "Forward Melt", "Forward Vaporize", "Reverse Melt", "Reverse Vaporize", "Superposition", 
        }

def get_amplifying_multiplier(reaction: str) -> float:
    return {
        "Forward Vaporize": 2.0,
        "Reverse Vaporize": 1.5,
        "Forward Melt": 2.0,
        "Reverse Melt": 1.5,
        "Superposition": 2.25,
    }.get(reaction, 1.0)

def get_transformative_multiplier(reaction: str) -> float:
    return {
        "Burgeon": 3,
        "Hyperbloom": 3,
        "Shatter": 3,
        "Overload": 2.75,
        "Electro-Charged": 2,
        "Superconduct": 1.5,
        "Pyro Swirl": 0.6,
        "Cryo Swirl": 0.6,
        "Hydro Swirl": 0.2,
        "Electro Swirl": 0.6,
        "Burning": 0.6,
        "Stasis": 2.25,
        "Ignition": 2.25,
        "Impulse": 2.25,
        "Anchor": 2.25,
        "Superposition": 3,
    }.get(reaction, 1.0)
