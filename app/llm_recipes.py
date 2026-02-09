from __future__ import annotations

import os
from typing import List, Dict, Any


def render_recipe_basic(title: str, ingredients: List[Dict[str, Any]], max_minutes: int = 35) -> str:
    lines = [f"{title}", f"Tempo stimato: {max_minutes} min", "", "Ingredienti:"]
    for ing in ingredients:
        lines.append(f"- {ing['name']}: {ing['grams']} g")
    lines.append("\nProcedimento:")
    lines.append("1) Prepara gli ingredienti (lava, taglia, pesa).")
    lines.append("2) Cuoci la componente proteica (se presente) con spezie e un filo d'olio.")
    lines.append("3) Cuoci la componente amidacea (riso/quinoa) e unisci alle verdure.")
    lines.append("4) Regola di sale, aggiungi spezie/erbe e servi.")
    lines.append("\nNote: spezie, erbe, limone e aceto sono considerati dispensa e non incidono sui calcoli.")
    return "\n".join(lines)

# Optional: integrate an LLM provider.
# For an MVP we keep this file provider-agnostic.

