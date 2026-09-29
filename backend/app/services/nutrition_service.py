"""Food search, logging, and daily totals. All numbers derive from stored foods (spec 10-22)."""
from datetime import date, timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.calculations.nutrition import meal_totals, scale_nutrients
from app.models.nutrition import (
    FavoriteFood, Food, Meal, MealItem, NutritionTarget, Recipe, RecipeIngredient,
)


PER100_KEYS = ("calories_kcal", "protein_g", "carbs_g", "fat_g")


def _per100(food: Food) -> dict:
    return {k: getattr(food, k) for k in PER100_KEYS}


def search_foods(db: Session, q: str, category: str | None = None, limit: int = 30) -> list[Food]:
    stmt = select(Food)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(or_(func.lower(Food.name).like(like), func.lower(Food.brand).like(like)))
    if category:
        stmt = stmt.where(Food.category == category)
    # Shortest matching name first: "Egg" beats "Egg white, dried".
    stmt = stmt.order_by(func.length(Food.name)).limit(limit)
    return list(db.scalars(stmt))


def get_or_create_meal(db: Session, user_id: int, logged_on: date, category: str) -> Meal:
    meal = db.scalar(
        select(Meal).where(
            Meal.user_id == user_id, Meal.logged_on == logged_on, Meal.category == category
        )
    )
    if meal is None:
        meal = Meal(user_id=user_id, logged_on=logged_on, category=category)
        db.add(meal)
        db.flush()
    return meal


def add_meal_item(
    db: Session, user_id: int, logged_on: date, category: str,
    food_id: int | None, recipe_id: int | None, quantity_g: float, serving_label: str | None,
) -> MealItem:
    """Snapshot the computed macros onto the item so history stays truthful (spec 86)."""
    if food_id is not None:
        food = db.get(Food, food_id)
        if food is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Food not found")
        values = scale_nutrients(_per100(food), quantity_g)
    elif recipe_id is not None:
        recipe = db.scalar(
            select(Recipe).options(selectinload(Recipe.ingredients)).where(Recipe.id == recipe_id)
        )
        if recipe is None or recipe.user_id != user_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Recipe not found")
        totals = recipe_totals_for(db, recipe)
        share = quantity_g / (recipe.total_weight_g or 100.0)
        values = {k: round(totals[k] * share, 2) for k in ("kcal", "protein_g", "carbs_g", "fat_g")}
    else:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Provide food_id or recipe_id")

    meal = get_or_create_meal(db, user_id, logged_on, category)
    item = MealItem(
        meal_id=meal.id, food_id=food_id, recipe_id=recipe_id, quantity_g=quantity_g,
        serving_label=serving_label, **values,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def recipe_totals_for(db: Session, recipe: Recipe) -> dict:
    ingredients = []
    for ing in recipe.ingredients:
        food = db.get(Food, ing.food_id)
        ingredients.append({"per_100g": _per100(food), "quantity_g": float(ing.quantity_g)})
    from app.calculations.nutrition import recipe_totals
    return recipe_totals(ingredients)


def day_totals(db: Session, user_id: int, day: date) -> dict:
    meals = list(
        db.scalars(
            select(Meal)
            .options(selectinload(Meal.items))
            .where(Meal.user_id == user_id, Meal.logged_on == day)
            .order_by(Meal.id)
        )
    )
    all_items = [{"kcal": i.kcal, "protein_g": i.protein_g, "carbs_g": i.carbs_g, "fat_g": i.fat_g}
                 for m in meals for i in m.items]
    totals = meal_totals(all_items)
    target = db.scalar(
        select(NutritionTarget)
        .where(NutritionTarget.user_id == user_id, NutritionTarget.effective_from <= day)
        .order_by(NutritionTarget.effective_from.desc())
    )
    totals.update({
        "logged_on": day,
        "target_kcal": float(target.kcal) if target else None,
        "target_protein_g": float(target.protein_g) if target else None,
        "target_carbs_g": float(target.carbs_g) if target else None,
        "target_fat_g": float(target.fat_g) if target else None,
        "meals": meals,
    })
    return totals


def history(db: Session, user_id: int, days: int) -> list[dict]:
    """Per-day totals for the last `days` days, oldest first. Missing days read as zero,
    and are reported as zero rather than invented (spec 22)."""
    start = date.today() - timedelta(days=days - 1)
    rows = db.execute(
        select(
            Meal.logged_on,
            func.coalesce(func.sum(MealItem.kcal), 0),
            func.coalesce(func.sum(MealItem.protein_g), 0),
            func.coalesce(func.sum(MealItem.carbs_g), 0),
            func.coalesce(func.sum(MealItem.fat_g), 0),
            func.count(MealItem.id),
        )
        .join(MealItem, MealItem.meal_id == Meal.id)
        .where(Meal.user_id == user_id, Meal.logged_on >= start)
        .group_by(Meal.logged_on)
    ).all()
    by_day = {r[0]: r for r in rows}
    out = []
    for i in range(days):
        d = start + timedelta(days=i)
        r = by_day.get(d)
        out.append({
            "date": d.isoformat(),
            "kcal": float(r[1]) if r else 0.0,
            "protein_g": float(r[2]) if r else 0.0,
            "carbs_g": float(r[3]) if r else 0.0,
            "fat_g": float(r[4]) if r else 0.0,
            "items": int(r[5]) if r else 0,
        })
    return out
