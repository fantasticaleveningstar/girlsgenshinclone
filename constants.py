from core import Element

ELEMENT_EMOJIS = {
    Element.PYRO: "🔥",
    Element.HYDRO: "💧",
    Element.ELECTRO: "⚡",
    Element.CRYO: "❄",
    Element.GEO: "🪨",
    Element.ANEMO: "💨",
    Element.DENDRO: "🌿",
    Element.QUANTUM: "🕳️",
    Element.IMAGINARY: "✨",
    Element.PHYSICAL: "💥",
}

ELEMENT_COLORS = {
    Element.PYRO: "\033[38;2;255;102;64m",
    Element.HYDRO: "\033[38;2;0;192;255m",
    Element.ELECTRO: "\033[38;2;204;128;255m",
    Element.CRYO: "\033[38;2;122;242;242m",
    Element.GEO: "\033[38;2;255;176;13m",
    Element.ANEMO: "\033[38;2;51;215;160m",
    Element.DENDRO: "\033[38;2;155;229;61m",
    Element.QUANTUM: "\033[38;2;111;102;221m",
    Element.IMAGINARY: "\033[38;2;212;189;77m",
    Element.PHYSICAL: "\033[97m",  # fallback bright white
}

class TextColor:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    GRAY = "\033[90m"
    WHITE = "\033[97m"
    HEAL = "\033[38;2;149;224;33m"

REACTION_EMOJIS = {
    "Forward Melt": "💥❄️🔥",
    "Reverse Melt": "❄️💥🔥",
    "Forward Vaporize": "💧🔥💨",
    "Reverse Vaporize": "🔥💧💨",
    "Overload": "💣🔥⚡",
    "Freeze": "❄️❄️💧",
    "Superconduct": "⚡❄️💥",
    "Superposition": "🔗🔮",
    "Burning": "🔥🌿",
    "Bloom": "🌸💧🌿",
}

REACTION_AURA_CONSUMPTION = {
    "Forward Melt": 2.0,
    "Reverse Melt": 0.5,
    "Forward Vaporize": 2.0,
    "Reverse Vaporize": 0.5,
    "Cryo Swirl": 0.5,
    "Pyro Swirl": 0.5,
    "Hydro Swirl": 0.5,
    "Electro Swirl": 0.5,
    "Overload": 1.0,
    "Superconduct": 1.0,
    "Burning": 0.5,
    "Bloom": 0.5,
    "Superposition": 2.0,
    "Rimegrass": 1.0,
    "Stasis": 1.0,
    # Add more if needed
}

