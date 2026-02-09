from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Optional

from app.nutrition import NutritionDB

OUT_PATH = Path(__file__).resolve().parents[1] / "data" / "recipes.json"

db = NutritionDB()

def key_of(query: str, prefer_substring: Optional[str] = None) -> str:
    """Return a food_key matching a query string."""
    results = db.search(query, limit=50)
    if not results:
        raise ValueError(f"No food matches query: {query}")
    if prefer_substring:
        for r in results:
            if prefer_substring.lower() in r["food"].lower():
                return r["food_key"]
    return results[0]["food_key"]

def nutrients_for_ingredients(ingredients: List[Dict]) -> Dict[str, float]:
    totals: Dict[str, float] = {}
    for ing in ingredients:
        fk = str(ing["food_key"])
        g = float(ing["grams"])
        n = db.nutrients_for_grams(fk, g)
        for k, v in n.items():
            totals[k] = totals.get(k, 0.0) + float(v)
    return totals

def make_recipe(recipe_id: str, title: str, meal_types: List[str], ingredients: List[Dict], tags: List[str]) -> Dict:
    return {
        "recipe_id": recipe_id,
        "title": title,
        "meal_types": meal_types,
        "tags": tags,
        "ingredients": ingredients,
        "nutrients_per_serving": nutrients_for_ingredients(ingredients),
    }

def main():
    # Pantry assumed: salt, pepper, spices, herbs, vinegar/lemon, water.
    # Goal: low gluten, low dairy, no refined sugar.

    foods = {
        "oats_dry": key_of("Cereals, oats, regular", "dry"),
        "egg_whole": key_of("Egg, whole, raw"),
        "egg_white": key_of("Egg, white, raw"),
        "banana": key_of("Bananas, raw") if db.search("Bananas, raw") else key_of("banana"),
        "apple": key_of("Apples, raw") if db.search("Apples, raw") else key_of("apple"),
        "blueberries": key_of("Blueberries"),
        "quinoa_dry": key_of("Quinoa, uncooked"),
        "rice_brown_dry": key_of("Rice, brown", "dry"),
        "lentils_cooked": key_of("Lentils", "boiled"),
        "chickpeas_cooked": key_of("Chickpeas", "boiled"),
        "tofu_firm": key_of("Tofu, firm"),
        "chicken_breast_raw": key_of("Chicken, broilers or fryers, breast", "raw"),
        "salmon_raw": key_of("Fish, salmon", "raw"),
        "tuna_canned": key_of("Fish, tuna", "canned in water") if db.search("canned in water") else key_of("Fish, tuna"),
        "olive_oil": key_of("Oil, olive"),
        "avocado": key_of("Avocados, raw"),
        "spinach": key_of("Spinach, raw"),
        "broccoli": key_of("Broccoli, raw"),
        "tomato": key_of("Tomatoes, red, ripe, raw"),
        "carrot": key_of("Carrots, raw"),
        "onion": key_of("Onions, raw"),
        "garlic": key_of("Garlic, raw"),
        "almonds": key_of("Almonds"),
        "walnuts": key_of("Walnuts"),
        "chia": key_of("Seeds, chia") if db.search("chia") else key_of("Seeds"),
        "yogurt": key_of("Yogurt, plain", "low fat"),
    }

    recipes: List[Dict] = []

    # Helper for compact definitions
    def R(rid, title, meal_types, ing, tags):
        recipes.append(make_recipe(rid, title, meal_types, ing, tags))

    # Breakfasts (10)
    R("b1", "Porridge d'avena con banana e mirtilli", ["breakfast"], [
        {"food_key": foods["oats_dry"], "grams": 60},
        {"food_key": foods["banana"], "grams": 120},
        {"food_key": foods["blueberries"], "grams": 80},
        {"food_key": foods["chia"], "grams": 10},
    ], ["low_gluten", "dairy_free", "no_refined_sugar"])

    R("b2", "Uova strapazzate con spinaci e avocado", ["breakfast"], [
        {"food_key": foods["egg_whole"], "grams": 120},
        {"food_key": foods["spinach"], "grams": 80},
        {"food_key": foods["avocado"], "grams": 70},
        {"food_key": foods["olive_oil"], "grams": 5},
    ], ["gluten_free", "low_dairy", "no_refined_sugar"])

    R("b3", "Yogurt con mela e noci", ["breakfast"], [
        {"food_key": foods["yogurt"], "grams": 200},
        {"food_key": foods["apple"], "grams": 150},
        {"food_key": foods["walnuts"], "grams": 20},
    ], ["gluten_free", "contains_dairy", "no_refined_sugar"])

    R("b4", "Frittata leggera albumi+uovo con pomodoro", ["breakfast"], [
        {"food_key": foods["egg_white"], "grams": 180},
        {"food_key": foods["egg_whole"], "grams": 60},
        {"food_key": foods["tomato"], "grams": 160},
        {"food_key": foods["olive_oil"], "grams": 5},
    ], ["gluten_free", "low_dairy", "no_refined_sugar"])

    R("b5", "Overnight oats con mela e mandorle", ["breakfast"], [
        {"food_key": foods["oats_dry"], "grams": 55},
        {"food_key": foods["apple"], "grams": 180},
        {"food_key": foods["chia"], "grams": 12},
        {"food_key": foods["almonds"], "grams": 15},
    ], ["low_gluten", "dairy_free", "no_refined_sugar"])

    R("b6", "Pudding di chia con yogurt e mirtilli", ["breakfast"], [
        {"food_key": foods["chia"], "grams": 25},
        {"food_key": foods["yogurt"], "grams": 180},
        {"food_key": foods["blueberries"], "grams": 120},
    ], ["gluten_free", "contains_dairy", "no_refined_sugar"])

    R("b7", "Omelette con broccoli e pomodoro", ["breakfast"], [
        {"food_key": foods["egg_whole"], "grams": 140},
        {"food_key": foods["broccoli"], "grams": 120},
        {"food_key": foods["tomato"], "grams": 120},
        {"food_key": foods["olive_oil"], "grams": 5},
    ], ["gluten_free", "low_dairy", "no_refined_sugar"])

    R("b8", "Uova e avocado con pomodori", ["breakfast"], [
        {"food_key": foods["egg_whole"], "grams": 120},
        {"food_key": foods["avocado"], "grams": 90},
        {"food_key": foods["tomato"], "grams": 180},
    ], ["gluten_free", "low_dairy", "no_refined_sugar"])

    R("b9", "Porridge d'avena con mela e noci", ["breakfast"], [
        {"food_key": foods["oats_dry"], "grams": 60},
        {"food_key": foods["apple"], "grams": 170},
        {"food_key": foods["walnuts"], "grams": 18},
    ], ["low_gluten", "dairy_free", "no_refined_sugar"])

    R("b10", "Yogurt con banana e chia", ["breakfast"], [
        {"food_key": foods["yogurt"], "grams": 220},
        {"food_key": foods["banana"], "grams": 140},
        {"food_key": foods["chia"], "grams": 12},
    ], ["gluten_free", "contains_dairy", "no_refined_sugar"])

    # Lunch/Dinner (22)
    R("m1", "Bowl quinoa, ceci, spinaci e pomodoro", ["lunch", "dinner"], [
        {"food_key": foods["quinoa_dry"], "grams": 70},
        {"food_key": foods["chickpeas_cooked"], "grams": 150},
        {"food_key": foods["spinach"], "grams": 80},
        {"food_key": foods["tomato"], "grams": 150},
        {"food_key": foods["olive_oil"], "grams": 10},
    ], ["gluten_free", "dairy_free", "no_refined_sugar", "veg"])

    R("m2", "Riso integrale con pollo e broccoli", ["lunch", "dinner"], [
        {"food_key": foods["rice_brown_dry"], "grams": 80},
        {"food_key": foods["chicken_breast_raw"], "grams": 160},
        {"food_key": foods["broccoli"], "grams": 200},
        {"food_key": foods["olive_oil"], "grams": 10},
    ], ["gluten_free", "dairy_free", "no_refined_sugar"])

    R("m3", "Salmone al forno con carote e spinaci", ["lunch", "dinner"], [
        {"food_key": foods["salmon_raw"], "grams": 170},
        {"food_key": foods["carrot"], "grams": 220},
        {"food_key": foods["spinach"], "grams": 80},
        {"food_key": foods["olive_oil"], "grams": 10},
    ], ["gluten_free", "dairy_free", "no_refined_sugar"])

    R("m4", "Tofu saltato con broccoli e riso", ["lunch", "dinner"], [
        {"food_key": foods["tofu_firm"], "grams": 220},
        {"food_key": foods["broccoli"], "grams": 220},
        {"food_key": foods["rice_brown_dry"], "grams": 70},
        {"food_key": foods["olive_oil"], "grams": 10},
    ], ["gluten_free", "dairy_free", "no_refined_sugar", "veg"])

    R("m5", "Insalata di tonno, avocado e pomodori", ["lunch", "dinner"], [
        {"food_key": foods["tuna_canned"], "grams": 160},
        {"food_key": foods["avocado"], "grams": 90},
        {"food_key": foods["tomato"], "grams": 220},
        {"food_key": foods["spinach"], "grams": 60},
        {"food_key": foods["olive_oil"], "grams": 10},
    ], ["gluten_free", "dairy_free", "no_refined_sugar"])

    R("m6", "Zuppa di lenticchie con spinaci", ["lunch", "dinner"], [
        {"food_key": foods["lentils_cooked"], "grams": 260},
        {"food_key": foods["spinach"], "grams": 90},
        {"food_key": foods["onion"], "grams": 60},
        {"food_key": foods["olive_oil"], "grams": 10},
    ], ["gluten_free", "dairy_free", "no_refined_sugar", "veg", "batch"])

    R("m7", "Quinoa con salmone e avocado", ["lunch", "dinner"], [
        {"food_key": foods["quinoa_dry"], "grams": 70},
        {"food_key": foods["salmon_raw"], "grams": 150},
        {"food_key": foods["avocado"], "grams": 80},
        {"food_key": foods["spinach"], "grams": 60},
        {"food_key": foods["olive_oil"], "grams": 10},
    ], ["gluten_free", "dairy_free", "no_refined_sugar"])

    R("m8", "Riso integrale con ceci e broccoli", ["lunch", "dinner"], [
        {"food_key": foods["rice_brown_dry"], "grams": 75},
        {"food_key": foods["chickpeas_cooked"], "grams": 180},
        {"food_key": foods["broccoli"], "grams": 220},
        {"food_key": foods["olive_oil"], "grams": 10},
    ], ["gluten_free", "dairy_free", "no_refined_sugar", "veg", "batch"])

    R("m9", "Pollo con quinoa e pomodori", ["lunch", "dinner"], [
        {"food_key": foods["chicken_breast_raw"], "grams": 170},
        {"food_key": foods["quinoa_dry"], "grams": 65},
        {"food_key": foods["tomato"], "grams": 220},
        {"food_key": foods["olive_oil"], "grams": 10},
    ], ["gluten_free", "dairy_free", "no_refined_sugar"])

    R("m10", "Tofu e spinaci con quinoa", ["lunch", "dinner"], [
        {"food_key": foods["tofu_firm"], "grams": 220},
        {"food_key": foods["spinach"], "grams": 120},
        {"food_key": foods["quinoa_dry"], "grams": 70},
        {"food_key": foods["olive_oil"], "grams": 10},
    ], ["gluten_free", "dairy_free", "no_refined_sugar", "veg"])

    R("m11", "Salmone con riso integrale e broccoli", ["lunch", "dinner"], [
        {"food_key": foods["salmon_raw"], "grams": 160},
        {"food_key": foods["rice_brown_dry"], "grams": 75},
        {"food_key": foods["broccoli"], "grams": 200},
        {"food_key": foods["olive_oil"], "grams": 10},
    ], ["gluten_free", "dairy_free", "no_refined_sugar"])

    R("m12", "Tonno con quinoa e pomodori", ["lunch", "dinner"], [
        {"food_key": foods["tuna_canned"], "grams": 160},
        {"food_key": foods["quinoa_dry"], "grams": 70},
        {"food_key": foods["tomato"], "grams": 200},
        {"food_key": foods["olive_oil"], "grams": 10},
    ], ["gluten_free", "dairy_free", "no_refined_sugar"])

    R("m13", "Ceci e spinaci con avocado", ["lunch", "dinner"], [
        {"food_key": foods["chickpeas_cooked"], "grams": 220},
        {"food_key": foods["spinach"], "grams": 120},
        {"food_key": foods["avocado"], "grams": 70},
        {"food_key": foods["olive_oil"], "grams": 10},
    ], ["gluten_free", "dairy_free", "no_refined_sugar", "veg"])

    R("m14", "Lenticchie con riso integrale", ["lunch", "dinner"], [
        {"food_key": foods["lentils_cooked"], "grams": 260},
        {"food_key": foods["rice_brown_dry"], "grams": 70},
        {"food_key": foods["onion"], "grams": 50},
        {"food_key": foods["olive_oil"], "grams": 10},
    ], ["gluten_free", "dairy_free", "no_refined_sugar", "veg", "batch"])

    R("m15", "Pollo con spinaci e pomodori", ["lunch", "dinner"], [
        {"food_key": foods["chicken_breast_raw"], "grams": 180},
        {"food_key": foods["spinach"], "grams": 140},
        {"food_key": foods["tomato"], "grams": 200},
        {"food_key": foods["olive_oil"], "grams": 10},
    ], ["gluten_free", "dairy_free", "no_refined_sugar"])

    R("m16", "Tofu con carote e broccoli", ["lunch", "dinner"], [
        {"food_key": foods["tofu_firm"], "grams": 240},
        {"food_key": foods["carrot"], "grams": 200},
        {"food_key": foods["broccoli"], "grams": 200},
        {"food_key": foods["olive_oil"], "grams": 10},
    ], ["gluten_free", "dairy_free", "no_refined_sugar", "veg"])

    R("m17", "Salmone con pomodori e spinaci", ["lunch", "dinner"], [
        {"food_key": foods["salmon_raw"], "grams": 170},
        {"food_key": foods["tomato"], "grams": 250},
        {"food_key": foods["spinach"], "grams": 90},
        {"food_key": foods["olive_oil"], "grams": 10},
    ], ["gluten_free", "dairy_free", "no_refined_sugar"])

    R("m18", "Tonno e broccoli con riso", ["lunch", "dinner"], [
        {"food_key": foods["tuna_canned"], "grams": 160},
        {"food_key": foods["broccoli"], "grams": 250},
        {"food_key": foods["rice_brown_dry"], "grams": 70},
        {"food_key": foods["olive_oil"], "grams": 10},
    ], ["gluten_free", "dairy_free", "no_refined_sugar"])

    R("m19", "Insalatona pollo-avocado-spinaci", ["lunch", "dinner"], [
        {"food_key": foods["chicken_breast_raw"], "grams": 160},
        {"food_key": foods["avocado"], "grams": 100},
        {"food_key": foods["spinach"], "grams": 120},
        {"food_key": foods["tomato"], "grams": 180},
        {"food_key": foods["olive_oil"], "grams": 10},
    ], ["gluten_free", "dairy_free", "no_refined_sugar"])

    R("m20", "Quinoa con lenticchie e pomodoro", ["lunch", "dinner"], [
        {"food_key": foods["quinoa_dry"], "grams": 65},
        {"food_key": foods["lentils_cooked"], "grams": 220},
        {"food_key": foods["tomato"], "grams": 220},
        {"food_key": foods["olive_oil"], "grams": 10},
    ], ["gluten_free", "dairy_free", "no_refined_sugar", "veg", "batch"])

    R("m21", "Ceci e avocado con pomodori", ["lunch", "dinner"], [
        {"food_key": foods["chickpeas_cooked"], "grams": 220},
        {"food_key": foods["avocado"], "grams": 90},
        {"food_key": foods["tomato"], "grams": 220},
        {"food_key": foods["olive_oil"], "grams": 10},
    ], ["gluten_free", "dairy_free", "no_refined_sugar", "veg"])

    R("m22", "Pollo con riso e carote", ["lunch", "dinner"], [
        {"food_key": foods["chicken_breast_raw"], "grams": 170},
        {"food_key": foods["rice_brown_dry"], "grams": 80},
        {"food_key": foods["carrot"], "grams": 220},
        {"food_key": foods["olive_oil"], "grams": 10},
    ], ["gluten_free", "dairy_free", "no_refined_sugar"])

    OUT_PATH.write_text(json.dumps(recipes, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(recipes)} recipes to {OUT_PATH}")

if __name__ == "__main__":
    main()
