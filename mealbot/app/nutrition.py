from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

import pandas as pd

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "nutrition.csv"

class NutritionDB:
    """Nutrition lookup. All nutrient values are per 100 g.

    The shipped dataset is a compact CSV (8,463 foods, 28 nutrient columns),
    commonly used in public educational material and derived from USDA food
    composition sources.
    """

    def __init__(self, csv_path: Optional[Path] = None):
        path = csv_path or DATA_PATH
        self.df = pd.read_csv(path)
        self.df["food"] = self.df["food"].astype(str)
        self.df["food_key"] = self.df["food"].str.lower().str.replace(r"[^a-z0-9]+", "_", regex=True).str.strip("_")
        self.df.set_index("food_key", inplace=True, drop=False)

        # Determine which nutrient columns are available
        self.nutrient_cols = [c for c in self.df.columns if c not in {"food", "food_key", "group"}]

    def has_food(self, food_key: str) -> bool:
        return food_key in self.df.index

    def get_food_row(self, food_key: str) -> Dict:
        if food_key not in self.df.index:
            raise KeyError(f"Unknown food_key: {food_key}")
        row = self.df.loc[food_key]
        out: Dict = {}
        for k, v in row.items():
            if k == "food":
                out[k] = str(v)
                continue
            if k == "food_key":
                out[k] = str(v)
                continue
            if k == "group":
                out[k] = str(v)
                continue
            if pd.isna(v):
                out[k] = None
            else:
                out[k] = float(v)
        return out

    def search(self, query: str, limit: int = 10):
        q = query.lower()
        m = self.df[self.df["food"].str.lower().str.contains(q, na=False)].head(limit)
        return m[["food", "food_key", "group"]].to_dict(orient="records")

    def nutrients_for_grams(self, food_key: str, grams: float) -> Dict[str, float]:
        """Return nutrient totals for a given amount in grams."""
        row = self.get_food_row(food_key)
        factor = grams / 100.0
        out: Dict[str, float] = {}
        for c in self.nutrient_cols:
            v = row.get(c)
            if v is None:
                continue
            out[c] = float(v) * factor
        return out
