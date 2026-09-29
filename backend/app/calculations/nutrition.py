"""Serving conversion and totals. Food rows store values per 100 g (spec 12, 13)."""


def scale_nutrients(per_100g: dict, grams: float) -> dict:
    """nutrition = nutrition_per_100g * grams / 100"""
    factor = grams / 100.0
    return {
        "kcal": round(float(per_100g.get("calories_kcal", 0)) * factor, 2),
        "protein_g": round(float(per_100g.get("protein_g", 0)) * factor, 2),
        "carbs_g": round(float(per_100g.get("carbs_g", 0)) * factor, 2),
        "fat_g": round(float(per_100g.get("fat_g", 0)) * factor, 2),
    }


def serving_to_grams(servings: float, serving_grams: float | None) -> float:
    """Convert a number of portions to grams using the food's OWN serving weight.
    We never assume one piece of every food weighs the same (spec 13)."""
    if serving_grams is None or serving_grams <= 0:
        raise ValueError("This food has no defined serving weight; log it in grams instead.")
    return round(servings * serving_grams, 2)


def meal_totals(items: list[dict]) -> dict:
    """Sum the per-item snapshot values stored at log time."""
    return {
        "kcal": round(sum(float(i.get("kcal", 0)) for i in items), 2),
        "protein_g": round(sum(float(i.get("protein_g", 0)) for i in items), 2),
        "carbs_g": round(sum(float(i.get("carbs_g", 0)) for i in items), 2),
        "fat_g": round(sum(float(i.get("fat_g", 0)) for i in items), 2),
    }


def recipe_totals(ingredients: list[dict]) -> dict:
    """ingredients: [{per_100g: {...}, quantity_g: n}]. Totals are derived, never typed in."""
    items = [scale_nutrients(i["per_100g"], float(i["quantity_g"])) for i in ingredients]
    return meal_totals(items)
