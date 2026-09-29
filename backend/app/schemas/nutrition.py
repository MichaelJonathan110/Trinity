from datetime import date
from pydantic import BaseModel, ConfigDict, Field


class FoodOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    brand: str | None
    category: str | None
    calories_kcal: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float | None
    default_serving_g: float | None
    default_serving_label: str | None
    data_quality: str
    source_ref: str | None


class FoodSearchOut(BaseModel):
    items: list[FoodOut]
    total: int
    query: str


class MealItemIn(BaseModel):
    food_id: int | None = None
    recipe_id: int | None = None
    quantity_g: float = Field(gt=0, le=5000)
    serving_label: str | None = None


class MealItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    food_id: int | None
    recipe_id: int | None
    quantity_g: float
    serving_label: str | None
    kcal: float
    protein_g: float
    carbs_g: float
    fat_g: float


class MealIn(BaseModel):
    logged_on: date
    category: str
    name: str | None = None


class MealOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    logged_on: date
    category: str
    name: str | None
    items: list[MealItemOut] = []


class DayTotalsOut(BaseModel):
    logged_on: date
    kcal: float
    protein_g: float
    carbs_g: float
    fat_g: float
    target_kcal: float | None
    target_protein_g: float | None
    target_carbs_g: float | None
    target_fat_g: float | None
    meals: list[MealOut]


class RecipeIn(BaseModel):
    name: str
    servings: int = Field(default=1, ge=1, le=50)
    ingredients: list[MealItemIn]


class RecipeOut(BaseModel):
    id: int
    name: str
    servings: int
    totals: dict
    per_serving: dict
