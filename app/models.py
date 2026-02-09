from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Literal

GlutenLimit = Literal["low", "very_low"]
DairyLimit = Literal["low", "none"]
RefinedSugar = Literal["avoid", "allow_small"]

DEFAULT_MACROS = {
    "protein": 120.0,
    "carbohydrates": 220.0,
    "total_fat": 70.0,
    "fiber": 30.0,
}

DEFAULT_MICROS = {
    # Units follow the underlying dataset columns.
    # sodium/calcium/iron/magnesium/phosphorus/potassium are mg
    # folic_acid is mcg, selenium is mcg, vitamin_A is IU-ish depending on source, vitamin_D is IU
    # For an MVP we keep them as provided and treat them as "targets" in the same unit.
    "calcium": 1000.0,
    "iron": 18.0,
    "magnesium": 400.0,
    "potassium": 3400.0,
    "vitamin_C": 90.0,
}

class DailyTargets(BaseModel):
    calories: Optional[float] = 2000.0
    macros_g: Dict[str, float] = Field(default_factory=lambda: DEFAULT_MACROS.copy())
    micros: Dict[str, float] = Field(default_factory=lambda: DEFAULT_MICROS.copy())

class Preferences(BaseModel):
    gluten_limit_level: GlutenLimit = "low"
    dairy_limit_level: DairyLimit = "low"
    refined_sugar: RefinedSugar = "avoid"
    disliked_foods: List[str] = Field(default_factory=list)
    max_prep_minutes: int = 35
    servings_per_meal: float = 1.0
    variety: int = 28  # approx unique recipes/month

class UserProfile(BaseModel):
    daily_targets: DailyTargets = Field(default_factory=DailyTargets)
    preferences: Preferences = Field(default_factory=Preferences)

class StartMonthRequest(BaseModel):
    month: str  # YYYY-MM
    user_profile: UserProfile = Field(default_factory=UserProfile)

class MealPlanItem(BaseModel):
    recipe_id: str
    servings: float

class DayPlan(BaseModel):
    date: str  # YYYY-MM-DD
    breakfast: MealPlanItem
    lunch: MealPlanItem
    dinner: MealPlanItem
    totals: Dict[str, float]

class MonthPlan(BaseModel):
    month: str
    days: List[DayPlan]

class GroceryItem(BaseModel):
    food_key: str
    name: str
    total_grams: float
    rounded_purchase_qty: Optional[str] = None
    notes: Optional[str] = None

class GroceryList(BaseModel):
    items: List[GroceryItem]

class StartMonthResponse(BaseModel):
    month_plan: MonthPlan
    grocery_list: GroceryList
    inventory: Dict[str, float]  # food_key -> grams_remaining

class CookMealRequest(BaseModel):
    date: str
    meal: Literal["breakfast", "lunch", "dinner"]

class CookMealResponse(BaseModel):
    recipe_id: str
    servings: float
    ingredients: List[Dict[str, float | str]]
    recipe_text: str
    inventory_after: Dict[str, float]


class ChatMessageRequest(BaseModel):
    """Simple chat wrapper over the API.

    This is *not* an LLM chat; it's a lightweight command interface
    that calls the existing endpoints.

    The Vite/React frontend calls this endpoint with:
      {"session_id": "...", "message": "..."}

    For backward compatibility with the older embedded HTML chat,
    we also accept the legacy field name `text`.
    """

    session_id: str = "default"
    message: Optional[str] = None
    # legacy
    text: Optional[str] = None

    month: Optional[str] = None  # YYYY-MM, optional convenience


class ChatAction(BaseModel):
    type: Literal["SHOW_GROCERY_LIST", "SHOW_DAY", "PLAN_MONTH"]
    payload: Optional[Dict[str, Any]] = None


class ChatMessageResponse(BaseModel):
    reply: str
    actions: Optional[List[ChatAction]] = None
    data: Optional[Dict[str, Any]] = None
