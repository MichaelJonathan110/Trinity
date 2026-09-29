"""Food catalogue, logging, recipes, targets, TDEE history (spec 10-22, 49)."""
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class FoodSource(Base, TimestampMixin):
    """Provenance for every food row. We never claim data is exact (spec 12)."""
    __tablename__ = "food_sources"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    url: Mapped[str | None] = mapped_column(String(255))
    license: Mapped[str | None] = mapped_column(String(120))
    notes: Mapped[str | None] = mapped_column(Text)


class Food(Base, TimestampMixin):
    """Nutrition per 100 g (weight foods) plus optional household serving."""
    __tablename__ = "foods"
    __table_args__ = (
        Index("ix_foods_name_lower", "name"),
        Index("ix_foods_brand", "brand"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    brand: Mapped[str | None] = mapped_column(String(120))
    category: Mapped[str | None] = mapped_column(String(64), index=True)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("food_sources.id", ondelete="SET NULL"))
    source_ref: Mapped[str | None] = mapped_column(String(64))      # upstream id, e.g. USDA fdcId
    calories_kcal: Mapped[float] = mapped_column(Numeric(7, 2), nullable=False)
    protein_g: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    carbs_g: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    fat_g: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    fiber_g: Mapped[float | None] = mapped_column(Numeric(6, 2))
    sugar_g: Mapped[float | None] = mapped_column(Numeric(6, 2))
    sodium_mg: Mapped[float | None] = mapped_column(Numeric(8, 2))
    default_serving_g: Mapped[float | None] = mapped_column(Numeric(7, 2))
    default_serving_label: Mapped[str | None] = mapped_column(String(48))  # "1 egg", "1 cup"
    data_quality: Mapped[str] = mapped_column(String(16), default="reported", nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    servings: Mapped[list["FoodServing"]] = relationship(back_populates="food", cascade="all, delete-orphan")


class FoodServing(Base, TimestampMixin):
    """Named portion with an explicit gram weight - never assume 1 piece = N g (spec 13)."""
    __tablename__ = "food_servings"
    id: Mapped[int] = mapped_column(primary_key=True)
    food_id: Mapped[int] = mapped_column(ForeignKey("foods.id", ondelete="CASCADE"), index=True)
    label: Mapped[str] = mapped_column(String(48), nullable=False)
    grams: Mapped[float] = mapped_column(Numeric(7, 2), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    food: Mapped["Food"] = relationship(back_populates="servings")


class FavoriteFood(Base, TimestampMixin):
    __tablename__ = "favorite_foods"
    __table_args__ = (UniqueConstraint("user_id", "food_id", name="uq_fav_user_food"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    food_id: Mapped[int] = mapped_column(ForeignKey("foods.id", ondelete="CASCADE"))
    sort_order: Mapped[int] = mapped_column(default=0, nullable=False)


class CustomFood(Base, TimestampMixin):
    __tablename__ = "custom_foods"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    food_id: Mapped[int | None] = mapped_column(ForeignKey("foods.id", ondelete="CASCADE"))


class Recipe(Base, TimestampMixin):
    """A user recipe; totals are derived from ingredients, never typed in (spec 15)."""
    __tablename__ = "recipes"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    total_weight_g: Mapped[float | None] = mapped_column(Numeric(8, 2))
    servings: Mapped[int] = mapped_column(default=1, nullable=False)

    ingredients: Mapped[list["RecipeIngredient"]] = relationship(
        back_populates="recipe", cascade="all, delete-orphan"
    )


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"
    id: Mapped[int] = mapped_column(primary_key=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id", ondelete="CASCADE"), index=True)
    food_id: Mapped[int] = mapped_column(ForeignKey("foods.id", ondelete="RESTRICT"))
    quantity_g: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)

    recipe: Mapped["Recipe"] = relationship(back_populates="ingredients")


class Meal(Base, TimestampMixin):
    """A logged meal on a day. Categories are user-extensible (spec 16)."""
    __tablename__ = "meals"
    __table_args__ = (Index("ix_meals_user_date", "user_id", "logged_on"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    logged_on: Mapped[date] = mapped_column(Date, nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)  # breakfast|lunch|dinner|snacks|pre_workout|post_workout
    name: Mapped[str | None] = mapped_column(String(120))

    items: Mapped[list["MealItem"]] = relationship(back_populates="meal", cascade="all, delete-orphan")


class MealItem(Base, TimestampMixin):
    __tablename__ = "meal_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    meal_id: Mapped[int] = mapped_column(ForeignKey("meals.id", ondelete="CASCADE"), index=True)
    food_id: Mapped[int | None] = mapped_column(ForeignKey("foods.id", ondelete="SET NULL"))
    recipe_id: Mapped[int | None] = mapped_column(ForeignKey("recipes.id", ondelete="SET NULL"))
    quantity_g: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    serving_label: Mapped[str | None] = mapped_column(String(48))
    # Snapshot of the computed values at log time so history stays truthful
    # even if the underlying food row is later corrected (spec 86).
    kcal: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    protein_g: Mapped[float] = mapped_column(Numeric(7, 2), nullable=False)
    carbs_g: Mapped[float] = mapped_column(Numeric(7, 2), nullable=False)
    fat_g: Mapped[float] = mapped_column(Numeric(7, 2), nullable=False)

    meal: Mapped["Meal"] = relationship(back_populates="items")


class NutritionTarget(Base, TimestampMixin):
    __tablename__ = "nutrition_targets"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    kcal: Mapped[float] = mapped_column(Numeric(7, 2), nullable=False)
    protein_g: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    carbs_g: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    fat_g: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    source: Mapped[str] = mapped_column(String(24), default="calculated", nullable=False)  # calculated|manual


class TdeeEstimate(Base, TimestampMixin):
    """Every estimate is stored with its inputs so it is auditable (spec 19)."""
    __tablename__ = "tdee_estimates"
    __table_args__ = (Index("ix_tdee_user_date", "user_id", "estimated_on"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    estimated_on: Mapped[date] = mapped_column(Date, nullable=False)
    method: Mapped[str] = mapped_column(String(32), nullable=False)   # mifflin_st_jeor_activity|adaptive
    bmr_kcal: Mapped[float] = mapped_column(Numeric(7, 2), nullable=False)
    activity_multiplier: Mapped[float | None] = mapped_column(Numeric(4, 2))
    tdee_kcal: Mapped[float] = mapped_column(Numeric(7, 2), nullable=False)
    confidence: Mapped[str] = mapped_column(String(16), default="low", nullable=False)  # low|medium|high
    days_of_data: Mapped[int] = mapped_column(default=0, nullable=False)
    inputs_json: Mapped[str | None] = mapped_column(Text)
