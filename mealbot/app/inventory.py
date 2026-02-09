from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional

from .planner import RecipeBook


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _load_packaging_rules() -> Dict[str, Any]:
    """Load packaging rules from data/packaging_rules.json.

    Edit that file to match your local retailers (pack sizes, egg boxes, etc.).
    """
    path = DATA_DIR / "packaging_rules.json"
    if not path.exists():
        return {"by_food_key": {}, "fallback": {}}
    return json.loads(path.read_text(encoding="utf-8"))


_PACKAGING = _load_packaging_rules()


def aggregate_grocery_list(month_plan: Dict[str, Any], recipe_book: RecipeBook) -> Dict[str, float]:
    """Return total grams per food_key required for the whole month."""
    totals: Dict[str, float] = {}
    for day in month_plan["days"]:
        for meal in ("breakfast", "lunch", "dinner"):
            rid = day[meal]["recipe_id"]
            servings = float(day[meal]["servings"])
            recipe = recipe_book.by_id[rid]
            for ing in recipe.ingredients:
                fk = str(ing["food_key"])
                g = float(ing["grams"])
                totals[fk] = totals.get(fk, 0.0) + g * servings
    return {k: round(v, 1) for k, v in totals.items()}


def _round_to_step(grams: float, step_g: float) -> float:
    return float(int(math.ceil(grams / step_g) * step_g))


def round_for_purchase(food_key: str, grams: float, food_name: Optional[str] = None) -> str:
    """Round grams to realistic 'buyable' quantities.

    Supports per-ingredient packaging rules in data/packaging_rules.json.
    Fallback behavior uses sensible gram steps and kg formatting.
    """
    grams = max(0.0, float(grams))
    rules = _PACKAGING.get("by_food_key", {}).get(food_key)

    # 1) Exact per-food rules
    if rules:
        rtype = rules.get("type")
        if rtype == "pack_grams":
            pack_g = float(rules["pack_size_g"])
            packs = int(math.ceil(grams / pack_g)) or 1
            total_g = packs * pack_g
            label = rules.get("label", f"{int(pack_g)} g")
            return f"{packs} x {label} (tot {int(total_g)} g)"

        if rtype == "count":
            unit_g = float(rules.get("unit_grams", 50.0))
            pack_n = int(rules.get("pack_size", 6))
            n = int(math.ceil(grams / unit_g)) or 1
            packs = int(math.ceil(n / pack_n))
            total_n = packs * pack_n
            unit_label = rules.get("unit_label", "pz")
            return f"{packs} x {pack_n} {unit_label} (tot {total_n} {unit_label})"

        if rtype == "kg":
            kg = grams / 1000.0
            return f"{kg:.1f} kg"

    # 2) Name-based gentle heuristics (useful for produce)
    name = (food_name or "").lower()
    if any(k in name for k in ["raw", "fresh", "fruit", "vegetable", "berries", "tomatoes", "apples", "bananas"]):
        kg = grams / 1000.0
        if kg >= 0.3:
            return f"{kg:.1f} kg"
        return f"{int(_round_to_step(grams, 50))} g"

    # 3) Fallback steps
    if grams < 60:
        return f"{int(math.ceil(grams))} g"
    if grams < 250:
        return f"{int(_round_to_step(grams, 25))} g"
    if grams < 1000:
        return f"{int(_round_to_step(grams, 50))} g"

    rounded_g = _round_to_step(grams, 100)
    kg = rounded_g / 1000.0
    if kg < 10:
        return f"{kg:.2f} kg"
    return f"{kg:.1f} kg"


def grocery_list_items(totals: Dict[str, float], nutrition_db) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for fk, g in totals.items():
        row = nutrition_db.get_food_row(fk)
        name = row["food"]
        items.append({
            "food_key": fk,
            "name": name,
            "total_grams": g,
            "rounded_purchase_qty": round_for_purchase(fk, g, food_name=name),
        })
    items.sort(key=lambda x: x["name"])
    return items


def apply_meal_to_inventory(recipe, servings: float, inventory: Dict[str, float]) -> Dict[str, float]:
    inv = inventory.copy()
    for ing in recipe.ingredients:
        fk = str(ing["food_key"])
        used = float(ing["grams"]) * float(servings)
        inv[fk] = round(max(0.0, float(inv.get(fk, 0.0)) - used), 1)
    return inv
