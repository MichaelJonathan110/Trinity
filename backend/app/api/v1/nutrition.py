"""Nutrition: food search, logging, recipes, favorites, targets, TDEE (spec 10-22)."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, get_profile
from app.database.session import get_db
from app.models.nutrition import (
    FavoriteFood, Food, FoodServing, MealItem, NutritionTarget, Recipe, RecipeIngredient,
)
from app.models.user import User
from app.schemas.nutrition import (
    DayTotalsOut, FoodOut, FoodSearchOut, MealIn, MealItemIn, MealOut, RecipeIn, RecipeOut,
)
from app.services import nutrition_service, tdee_service
from app.integrations import usda

router = APIRouter(prefix="/nutrition", tags=["nutrition"])


@router.get("/foods", response_model=FoodSearchOut)
def search_foods(
    q: str = Query(default="", max_length=80),
    category: str | None = None,
    limit: int = Query(default=30, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    items = nutrition_service.search_foods(db, q, category, limit)
    return {"items": items, "total": len(items), "query": q}


@router.get("/foods/{food_id}")
def get_food(
    food_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    food = db.scalar(select(Food).options(selectinload(Food.servings)).where(Food.id == food_id))
    if food is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Food not found")
    return {
        "id": food.id, "name": food.name, "brand": food.brand, "category": food.category,
        "calories_kcal": float(food.calories_kcal), "protein_g": float(food.protein_g),
        "carbs_g": float(food.carbs_g), "fat_g": float(food.fat_g),
        "fiber_g": float(food.fiber_g) if food.fiber_g is not None else None,
        "data_quality": food.data_quality, "source_ref": food.source_ref,
        "servings": [{"id": s.id, "label": s.label, "grams": float(s.grams), "is_default": s.is_default}
                     for s in food.servings],
    }


@router.post("/foods", response_model=FoodOut, status_code=status.HTTP_201_CREATED)
def create_custom_food(
    payload: dict, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> object:
    """User-created food. Marked as such so it is never confused with reference data (spec 15)."""
    required = ("name", "calories_kcal", "protein_g", "carbs_g", "fat_g")
    missing = [k for k in required if payload.get(k) in (None, "")]
    if missing:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Missing fields: {', '.join(missing)}")
    food = Food(
        name=str(payload["name"])[:200], brand=payload.get("brand"), category=payload.get("category") or "custom",
        calories_kcal=float(payload["calories_kcal"]), protein_g=float(payload["protein_g"]),
        carbs_g=float(payload["carbs_g"]), fat_g=float(payload["fat_g"]),
        fiber_g=payload.get("fiber_g"), default_serving_g=payload.get("default_serving_g"),
        default_serving_label=payload.get("default_serving_label"),
        data_quality="user_entered", created_by_user_id=user.id,
    )
    db.add(food)
    db.commit()
    db.refresh(food)
    return food


@router.post("/foods/import-usda", status_code=status.HTTP_201_CREATED)
def import_usda(
    q: str = Query(min_length=2, max_length=80),
    limit: int = Query(default=5, ge=1, le=25),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Import real records from USDA FoodData Central.
    Requires USDA_API_KEY in the environment (spec 12). If the key is absent we say so
    plainly rather than returning invented food data."""
    try:
        records = usda.search_foods(q, limit)
    except usda.UsdaNotConfigured:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "USDA import is not configured. Set USDA_API_KEY to enable it. "
            "Seed reference foods remain available for development.",
        )
    except usda.UsdaError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"USDA request failed: {exc}")

    created = 0
    source_id = usda.ensure_source(db)
    for rec in records:
        if db.scalar(select(Food).where(Food.source_ref == rec["source_ref"])):
            continue
        db.add(Food(source_id=source_id, **rec))
        created += 1
    db.commit()
    return {"requested": q, "returned": len(records), "imported": created}


@router.get("/day", response_model=DayTotalsOut)
def day_totals(
    day: date | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return nutrition_service.day_totals(db, user.id, day or date.today())


@router.get("/history")
def nutrition_history(
    days: int = Query(default=30, ge=1, le=400),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list:
    return nutrition_service.history(db, user.id, days)


@router.post("/meals/items", status_code=status.HTTP_201_CREATED)
def add_item(
    payload: MealItemIn,
    logged_on: date,
    category: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    item = nutrition_service.add_meal_item(
        db, user.id, logged_on, category, payload.food_id, payload.recipe_id,
        payload.quantity_g, payload.serving_label,
    )
    return {"id": item.id, "kcal": float(item.kcal), "protein_g": float(item.protein_g),
            "carbs_g": float(item.carbs_g), "fat_g": float(item.fat_g)}


@router.delete("/meals/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> None:
    item = db.get(MealItem, item_id)
    if item is None or item.meal.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entry not found")
    db.delete(item)
    db.commit()


@router.get("/favorites")
def list_favorites(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list:
    rows = db.scalars(
        select(FavoriteFood).where(FavoriteFood.user_id == user.id).order_by(FavoriteFood.sort_order)
    )
    return [
        {"id": f.id, "food_id": f.food_id, "name": f.food.name if f.food else None,
         "sort_order": f.sort_order}
        for f in rows
    ]


@router.post("/favorites", status_code=status.HTTP_201_CREATED)
def add_favorite(
    food_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    if db.get(Food, food_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Food not found")
    existing = db.scalar(
        select(FavoriteFood).where(FavoriteFood.user_id == user.id, FavoriteFood.food_id == food_id)
    )
    if existing:
        return {"id": existing.id, "food_id": food_id}
    count = len(db.scalars(select(FavoriteFood).where(FavoriteFood.user_id == user.id)).all())
    fav = FavoriteFood(user_id=user.id, food_id=food_id, sort_order=count)
    db.add(fav)
    db.commit()
    db.refresh(fav)
    return {"id": fav.id, "food_id": food_id}


@router.delete("/favorites/{food_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_favorite(
    food_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> None:
    fav = db.scalar(
        select(FavoriteFood).where(FavoriteFood.user_id == user.id, FavoriteFood.food_id == food_id)
    )
    if fav is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not a favorite")
    db.delete(fav)
    db.commit()


@router.get("/recipes")
def list_recipes(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list:
    rows = db.scalars(
        select(Recipe).options(selectinload(Recipe.ingredients)).where(Recipe.user_id == user.id)
    )
    return [
        {"id": r.id, "name": r.name, "servings": r.servings,
         "total_weight_g": float(r.total_weight_g) if r.total_weight_g else None,
         "totals": nutrition_service.recipe_totals_for(db, r)}
        for r in rows
    ]


@router.post("/recipes", response_model=RecipeOut, status_code=status.HTTP_201_CREATED)
def create_recipe(
    payload: RecipeIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    recipe = Recipe(user_id=user.id, name=payload.name, servings=payload.servings)
    db.add(recipe)
    db.flush()
    total_weight = 0.0
    for ing in payload.ingredients:
        if ing.food_id is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Each ingredient needs a food_id")
        if db.get(Food, ing.food_id) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Food {ing.food_id} not found")
        db.add(RecipeIngredient(recipe_id=recipe.id, food_id=ing.food_id, quantity_g=ing.quantity_g))
        total_weight += ing.quantity_g
    recipe.total_weight_g = round(total_weight, 2)
    db.commit()
    db.refresh(recipe)
    db.refresh(recipe, ["ingredients"])
    totals = nutrition_service.recipe_totals_for(db, recipe)
    per_serving = {k: round(v / recipe.servings, 2) for k, v in totals.items()}
    return {"id": recipe.id, "name": recipe.name, "servings": recipe.servings,
            "totals": totals, "per_serving": per_serving}


@router.delete("/recipes/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recipe(
    recipe_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> None:
    recipe = db.get(Recipe, recipe_id)
    if recipe is None or recipe.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Recipe not found")
    db.delete(recipe)
    db.commit()


@router.get("/targets")
def get_targets(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    target = db.scalar(
        select(NutritionTarget)
        .where(NutritionTarget.user_id == user.id)
        .order_by(NutritionTarget.effective_from.desc())
    )
    if target is None:
        return {"exists": False, "note": "No nutrition target set yet. Calculate one from your profile."}
    return {
        "exists": True, "effective_from": target.effective_from.isoformat(),
        "kcal": float(target.kcal), "protein_g": float(target.protein_g),
        "carbs_g": float(target.carbs_g), "fat_g": float(target.fat_g), "source": target.source,
    }


@router.post("/targets/manual", status_code=status.HTTP_201_CREATED)
def set_targets_manual(
    payload: dict, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    """Manual override. The user is always allowed to set their own numbers (spec 20)."""
    try:
        target = NutritionTarget(
            user_id=user.id, effective_from=date.today(),
            kcal=float(payload["kcal"]), protein_g=float(payload["protein_g"]),
            carbs_g=float(payload["carbs_g"]), fat_g=float(payload["fat_g"]), source="manual",
        )
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            "kcal, protein_g, carbs_g and fat_g are all required numbers")
    db.add(target)
    db.commit()
    return {"ok": True, "effective_from": target.effective_from.isoformat()}


@router.get("/tdee")
def tdee(
    profile=Depends(get_profile), user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    result = tdee_service.compute(db, user.id, profile)
    if not result.get("ready"):
        return result
    history = list(
        db.scalars(
            select(NutritionTarget)
            .where(NutritionTarget.user_id == user.id)
            .order_by(NutritionTarget.effective_from.desc())
            .limit(20)
        )
    )
    result["target_history"] = [
        {"effective_from": t.effective_from.isoformat(), "kcal": float(t.kcal), "source": t.source}
        for t in history
    ]
    return result


@router.post("/tdee/apply", status_code=status.HTTP_201_CREATED)
def apply_tdee(
    profile=Depends(get_profile), user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Persist the estimate and set it as the active nutrition target."""
    result = tdee_service.compute(db, user.id, profile)
    if not result.get("ready"):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            f"Profile incomplete: missing {', '.join(result['missing'])}")
    tdee_service.persist(db, user.id, result)
    target = tdee_service.apply_targets(db, user.id, result)
    return {"ok": True, "kcal": float(target.kcal), "protein_g": float(target.protein_g),
            "carbs_g": float(target.carbs_g), "fat_g": float(target.fat_g),
            "estimate": result["adaptive"]}
