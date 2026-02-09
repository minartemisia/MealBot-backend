from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Tuple, Any

import json
from pathlib import Path

from .nutrition import NutritionDB

RECIPES_PATH = Path(__file__).resolve().parents[1] / "data" / "recipes.json"

@dataclass
class Recipe:
    recipe_id: str
    title: str
    meal_types: List[str]
    tags: List[str]
    ingredients: List[Dict[str, Any]]
    nutrients_per_serving: Dict[str, float]

class RecipeBook:
    def __init__(self, path: Path = RECIPES_PATH):
        data = json.loads(path.read_text(encoding="utf-8"))
        self.recipes: List[Recipe] = [Recipe(**r) for r in data]
        self.by_id = {r.recipe_id: r for r in self.recipes}

    def for_meal(self, meal: str) -> List[Recipe]:
        return [r for r in self.recipes if meal in r.meal_types]


def month_dates(yyyy_mm: str) -> List[str]:
    y, m = map(int, yyyy_mm.split("-"))
    last = calendar.monthrange(y, m)[1]
    return [date(y, m, d).isoformat() for d in range(1, last + 1)]


def _macro_targets_for_meal(daily_macros: Dict[str, float], meal: str) -> Dict[str, float]:
    split = {"breakfast": 0.25, "lunch": 0.35, "dinner": 0.40}[meal]
    return {k: float(v) * split for k, v in daily_macros.items()}


def _distance(recipe_macros: Dict[str, float], target: Dict[str, float]) -> float:
    # normalized L1
    d = 0.0
    for k, t in target.items():
        if k not in recipe_macros:
            continue
        v = float(recipe_macros.get(k, 0.0))
        d += abs(v - t) / max(float(t), 1e-6)
    return d


def _penalty(recipe: Recipe, prefs: Dict[str, str]) -> float:
    pen = 0.0
    tags = set(recipe.tags)

    # refined sugar
    if prefs.get("refined_sugar") == "avoid" and "refined_sugar" in tags:
        pen += 1000.0

    # dairy
    if prefs.get("dairy_limit_level") == "none" and "contains_dairy" in tags:
        pen += 1000.0
    elif prefs.get("dairy_limit_level") == "low" and "contains_dairy" in tags:
        pen += 4.0

    # gluten
    if prefs.get("gluten_limit_level") == "very_low" and "low_gluten" in tags:
        pen += 2.0
    if prefs.get("gluten_limit_level") == "very_low" and "gluten_free" not in tags:
        pen += 10.0
    return pen


def choose_recipe(recipes: List[Recipe], target_macros: Dict[str, float], prefs: Dict[str, str], recent_ids: List[str]) -> Recipe:
    best: Tuple[float, Recipe] | None = None
    for r in recipes:
        if r.recipe_id in recent_ids:
            continue
        r_macros = {
            "protein": r.nutrients_per_serving.get("protein", 0.0),
            "carbohydrates": r.nutrients_per_serving.get("carbohydrates", 0.0),
            "total_fat": r.nutrients_per_serving.get("total_fat", 0.0),
            "fiber": r.nutrients_per_serving.get("fiber", 0.0),
        }
        score = _distance(r_macros, target_macros) + _penalty(r, prefs)
        if best is None or score < best[0]:
            best = (score, r)
    # fallback allow repeats
    if best is None:
        r = recipes[0]
        return r
    return best[1]


def scale_servings(recipe: Recipe, target_macros: Dict[str, float]) -> float:
    # prioritize protein, clamp
    p = float(recipe.nutrients_per_serving.get("protein", 1.0))
    tp = float(target_macros.get("protein", p))
    s = tp / max(p, 1e-6)
    return max(0.6, min(1.6, s))


def sum_nutrients(items: List[Tuple[Recipe, float]]) -> Dict[str, float]:
    totals: Dict[str, float] = {}
    for r, s in items:
        for k, v in r.nutrients_per_serving.items():
            totals[k] = totals.get(k, 0.0) + float(v) * s
    # round
    return {k: round(v, 2) for k, v in totals.items()}


def build_month_plan(yyyy_mm: str, user_profile: Dict[str, Any]) -> Dict[str, Any]:
    prefs = user_profile["preferences"]
    daily_targets = user_profile["daily_targets"]
    daily_macros = daily_targets["macros_g"]

    book = RecipeBook()
    dates = month_dates(yyyy_mm)

    recent: List[str] = []
    days = []

    for d in dates:
        day_items = {}
        chosen: List[Tuple[Recipe, float]] = []
        for meal in ["breakfast", "lunch", "dinner"]:
            target = _macro_targets_for_meal(daily_macros, meal)
            r = choose_recipe(book.for_meal(meal), target, prefs, recent_ids=recent[-8:])
            s = round(scale_servings(r, target), 2)
            day_items[meal] = {"recipe_id": r.recipe_id, "servings": s}
            chosen.append((r, s))
            recent.append(r.recipe_id)

        totals = sum_nutrients(chosen)
        days.append({"date": d, **day_items, "totals": totals})

    return {"month": yyyy_mm, "days": days}
