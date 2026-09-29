"""USDA FoodData Central client (spec 12, 25).

Requires USDA_API_KEY. Without it we raise UsdaNotConfigured instead of inventing data.
Docs: https://fdc.nal.usda.gov/api-guide.html - the key is a free personal key.
"""
import os

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.nutrition import Food, FoodSource

BASE = "https://api.nal.usda.gov/fdc/v1/foods/search"
SOURCE_NAME = "USDA FoodData Central"

# FDC nutrient ids -> our columns (per 100 g basis, as returned by FDC).
NUTRIENT_MAP = {
    1008: "calories_kcal",   # Energy (kcal)
    1003: "protein_g",       # Protein
    1005: "carbs_g",         # Carbohydrate, by difference
    1004: "fat_g",           # Total lipid (fat)
    1079: "fiber_g",         # Fiber, total dietary
    2000: "sugar_g",         # Sugars, total
    1093: "sodium_mg",       # Sodium, Na
}


class UsdaNotConfigured(RuntimeError):
    pass


class UsdaError(RuntimeError):
    pass


def _key() -> str:
    key = os.getenv("USDA_API_KEY", "").strip()
    if not key:
        raise UsdaNotConfigured("USDA_API_KEY is not set")
    return key


def ensure_source(db: Session) -> int:
    row = db.scalar(select(FoodSource).where(FoodSource.name == SOURCE_NAME))
    if row is None:
        row = FoodSource(
            name=SOURCE_NAME, url="https://fdc.nal.usda.gov",
            license="Public domain (US Government work)",
            notes="Values are per 100 g and vary by brand, cut and preparation.",
        )
        db.add(row)
        db.flush()
    return row.id


def search_foods(query: str, limit: int = 5) -> list[dict]:
    """Return normalised food dicts, ready to insert. Raises on configuration or transport error."""
    params = {
        "api_key": _key(), "query": query, "pageSize": limit,
        "dataType": "Foundation,SR Legacy,Branded",
    }
    try:
        resp = httpx.get(BASE, params=params, timeout=15.0)
        resp.raise_for_status()
        payload = resp.json()
    except httpx.HTTPStatusError as exc:
        raise UsdaError(f"upstream returned {exc.response.status_code}") from exc
    except httpx.HTTPError as exc:
        raise UsdaError(f"network error: {exc}") from exc

    out = []
    for food in payload.get("foods", []):
        values = {v: 0.0 for v in NUTRIENT_MAP.values()}
        for n in food.get("foodNutrients", []):
            nid = n.get("nutrientId")
            if nid in NUTRIENT_MAP and n.get("value") is not None:
                values[NUTRIENT_MAP[nid]] = float(n["value"])
        if values["calories_kcal"] <= 0:
            continue  # skip records with no energy value rather than guessing one
        out.append({
            "name": (food.get("description") or "Unknown")[:200],
            "brand": (food.get("brandOwner") or food.get("brandName") or None),
            "category": (food.get("foodCategory") or None),
            "source_ref": str(food.get("fdcId")),
            "calories_kcal": values["calories_kcal"],
            "protein_g": values["protein_g"],
            "carbs_g": values["carbs_g"],
            "fat_g": values["fat_g"],
            "fiber_g": values["fiber_g"] or None,
            "sugar_g": values["sugar_g"] or None,
            "sodium_mg": values["sodium_mg"] or None,
            "default_serving_g": 100.0,
            "default_serving_label": "100 g",
            "data_quality": "usda_reported",
            "is_verified": True,
        })
    return out
