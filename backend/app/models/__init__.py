"""All ORM models. Importing this module registers every table on Base.metadata."""
from app.models.user import User, Profile, BodyMetric, Goal, ProgressPhoto, ConnectedHealthSource
from app.models.auth import PasswordResetToken
from app.models.notifications import NotificationPreference
from app.models.nutrition import (
    FoodSource, Food, FoodServing, FavoriteFood, CustomFood, Recipe, RecipeIngredient,
    Meal, MealItem, NutritionTarget, TdeeEstimate,
)
from app.models.training import (
    ExerciseLibrary, TrainingProgram, TrainingProgramDay, Workout, WorkoutExercise,
    ExerciseSet, ExerciseNote, PersonalRecord,
)
from app.models.prep import PreparationPhase, RefeedEntry
from app.models.recovery import SleepGoal, SleepSession, RecoveryMetric
from app.models.activity import StepRecord, DailyActivity
from app.models.insight import PerformanceInsight, Notification

__all__ = [
    "User", "Profile", "BodyMetric", "Goal", "ProgressPhoto", "ConnectedHealthSource",
    "PasswordResetToken", "NotificationPreference",
    "FoodSource", "Food", "FoodServing", "FavoriteFood", "CustomFood",
    "Recipe", "RecipeIngredient", "Meal", "MealItem", "NutritionTarget", "TdeeEstimate",
    "ExerciseLibrary", "TrainingProgram", "TrainingProgramDay", "Workout",
    "WorkoutExercise", "ExerciseSet", "ExerciseNote", "PersonalRecord",
    "PreparationPhase", "RefeedEntry",
    "SleepGoal", "SleepSession", "RecoveryMetric",
    "StepRecord", "DailyActivity", "PerformanceInsight", "Notification",
]
