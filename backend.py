from __future__ import annotations

import json
from abc import ABC
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class Unit(Enum):
    COUNT = "count"
    G = "g"
    KG = "kg"
    ML = "ml"
    L = "l"
    CUP = "cup"
    TBSP = "tbsp"
    TSP = "tsp"


class Difficulty(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class IngredientCategory(Enum):
    VEGETABLE = "vegetable"
    PROTEIN = "protein"
    GRAIN = "grain"
    DAIRY = "dairy"
    FRUIT = "fruit"
    SPICE = "spice"
    FAT = "fat"
    SAUCE = "sauce"
    OTHER = "other"


@dataclass
class Ingredient(ABC):
    name: str
    category: IngredientCategory
    prep_time_minutes: int = 0
    cooking_methods: List[str] = field(default_factory=list)
    perishability_days: Optional[int] = None

    def matches_name(self, other_name: str) -> bool:
        return self.name.strip().lower() == other_name.strip().lower()


@dataclass
class Vegetable(Ingredient):
    category: IngredientCategory = IngredientCategory.VEGETABLE


@dataclass
class Protein(Ingredient):
    category: IngredientCategory = IngredientCategory.PROTEIN


@dataclass
class Grain(Ingredient):
    category: IngredientCategory = IngredientCategory.GRAIN


@dataclass
class Dairy(Ingredient):
    category: IngredientCategory = IngredientCategory.DAIRY


@dataclass
class Fruit(Ingredient):
    category: IngredientCategory = IngredientCategory.FRUIT


@dataclass
class Spice(Ingredient):
    category: IngredientCategory = IngredientCategory.SPICE


@dataclass
class Fat(Ingredient):
    category: IngredientCategory = IngredientCategory.FAT


@dataclass
class Sauce(Ingredient):
    category: IngredientCategory = IngredientCategory.SAUCE


@dataclass
class OtherIngredient(Ingredient):
    category: IngredientCategory = IngredientCategory.OTHER


class IngredientFactory:
    @staticmethod
    def create_ingredient(
        name: str,
        category: IngredientCategory,
        prep_time_minutes: int = 0,
        cooking_methods: Optional[List[str]] = None,
        perishability_days: Optional[int] = None,
    ) -> Ingredient:
        cooking_methods = cooking_methods or []

        category_map = {
            IngredientCategory.VEGETABLE: Vegetable,
            IngredientCategory.PROTEIN: Protein,
            IngredientCategory.GRAIN: Grain,
            IngredientCategory.DAIRY: Dairy,
            IngredientCategory.FRUIT: Fruit,
            IngredientCategory.SPICE: Spice,
            IngredientCategory.FAT: Fat,
            IngredientCategory.SAUCE: Sauce,
            IngredientCategory.OTHER: OtherIngredient,
        }

        ingredient_cls = category_map.get(category, OtherIngredient)
        return ingredient_cls(
            name=name,
            prep_time_minutes=prep_time_minutes,
            cooking_methods=cooking_methods,
            perishability_days=perishability_days,
        )


@dataclass
class PantryItem:
    ingredient: Ingredient
    quantity: float
    unit: Unit

    def has_enough(self, required_quantity: float, required_unit: Unit) -> bool:
        if self.unit != required_unit:
            return False
        return self.quantity >= required_quantity


class Pantry:
    def __init__(self) -> None:
        self.items: Dict[str, PantryItem] = {}

    def add_item(self, pantry_item: PantryItem) -> None:
        key = pantry_item.ingredient.name.lower()

        if key in self.items and self.items[key].unit == pantry_item.unit:
            self.items[key].quantity += pantry_item.quantity
        else:
            self.items[key] = pantry_item

    def remove_item(self, ingredient_name: str) -> bool:
        key = ingredient_name.lower()
        if key in self.items:
            del self.items[key]
            return True
        return False

    def update_quantity(self, ingredient_name: str, quantity: float) -> bool:
        key = ingredient_name.lower()
        if key in self.items:
            self.items[key].quantity = quantity
            return True
        return False

    def get_item(self, ingredient_name: str) -> Optional[PantryItem]:
        return self.items.get(ingredient_name.lower())

    def list_items(self) -> List[PantryItem]:
        return list(self.items.values())


class PantryDatabase:
    def __init__(self, file_path: str = "pantry.json") -> None:
        self.file_path = Path(file_path)

    def add_ingredient(
        self,
        pantry: Pantry,
        name: str,
        quantity: float,
        unit: Unit,
        category: IngredientCategory,
        prep_time_minutes: int = 0,
        cooking_methods: Optional[List[str]] = None,
        perishability_days: Optional[int] = None,
    ) -> PantryItem:
        ingredient = IngredientFactory.create_ingredient(
            name=name,
            category=category,
            prep_time_minutes=prep_time_minutes,
            cooking_methods=cooking_methods,
            perishability_days=perishability_days,
        )
        pantry_item = PantryItem(ingredient=ingredient, quantity=quantity, unit=unit)
        pantry.add_item(pantry_item)
        self.save_pantry(pantry)
        return pantry_item

    def save_pantry(self, pantry: Pantry) -> None:
        payload = {"items": [self._serialize_pantry_item(item) for item in pantry.list_items()]}

        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        with self.file_path.open("w", encoding="utf-8") as db_file:
            json.dump(payload, db_file, indent=2)

    def load_pantry(self) -> Pantry:
        pantry = Pantry()
        if not self.file_path.exists():
            return pantry

        with self.file_path.open("r", encoding="utf-8") as db_file:
            payload = json.load(db_file)

        for raw_item in payload.get("items", []):
            pantry_item = self._deserialize_pantry_item(raw_item)
            if pantry_item is not None:
                pantry.add_item(pantry_item)

        return pantry

    def _serialize_pantry_item(self, pantry_item: PantryItem) -> Dict[str, Any]:
        return {
            "ingredient": {
                "name": pantry_item.ingredient.name,
                "category": pantry_item.ingredient.category.value,
                "prep_time_minutes": pantry_item.ingredient.prep_time_minutes,
                "cooking_methods": pantry_item.ingredient.cooking_methods,
                "perishability_days": pantry_item.ingredient.perishability_days,
            },
            "quantity": pantry_item.quantity,
            "unit": pantry_item.unit.value,
        }

    def _deserialize_pantry_item(self, raw_item: Dict[str, Any]) -> Optional[PantryItem]:
        raw_ingredient = raw_item.get("ingredient", {})
        name = raw_ingredient.get("name")
        if not name:
            return None

        category = self._parse_category(raw_ingredient.get("category"))
        unit = self._parse_unit(raw_item.get("unit"))
        ingredient = IngredientFactory.create_ingredient(
            name=name,
            category=category,
            prep_time_minutes=int(raw_ingredient.get("prep_time_minutes", 0)),
            cooking_methods=list(raw_ingredient.get("cooking_methods") or []),
            perishability_days=raw_ingredient.get("perishability_days"),
        )
        return PantryItem(
            ingredient=ingredient,
            quantity=float(raw_item.get("quantity", 0)),
            unit=unit,
        )

    def _parse_category(self, value: Any) -> IngredientCategory:
        try:
            return IngredientCategory(str(value))
        except ValueError:
            return IngredientCategory.OTHER

    def _parse_unit(self, value: Any) -> Unit:
        try:
            return Unit(str(value))
        except ValueError:
            return Unit.COUNT


@dataclass
class RecipeIngredient:
    ingredient_name: str
    quantity: float
    unit: Unit
    optional: bool = False


@dataclass
class Recipe:
    name: str
    ingredients: List[RecipeIngredient]
    steps: List[str]
    difficulty: Difficulty
    estimated_time_minutes: int

    def match_rate(self, pantry: Pantry) -> float:
        if not self.ingredients:
            return 0.0

        matched = 0
        required_items = [ri for ri in self.ingredients if not ri.optional]

        if not required_items:
            return 1.0

        for req in required_items:
            pantry_item = pantry.get_item(req.ingredient_name)
            if pantry_item and pantry_item.has_enough(req.quantity, req.unit):
                matched += 1

        return matched / len(required_items)

    def missing_ingredients(self, pantry: Pantry) -> List[RecipeIngredient]:
        missing = []
        for req in self.ingredients:
            pantry_item = pantry.get_item(req.ingredient_name)
            if req.optional:
                continue
            if pantry_item is None or not pantry_item.has_enough(req.quantity, req.unit):
                missing.append(req)
        return missing


from meal_templates import (
    BreakfastBowlTemplate,
    GrainVegBowlTemplate,
    MealRecommendation,
    MealTemplate,
    ProteinPlateTemplate,
    StirFryTemplate,
)


class MealGenerator:
    def __init__(self, templates: Optional[List[MealTemplate]] = None) -> None:
        self.templates = templates or [
            GrainVegBowlTemplate(),
            ProteinPlateTemplate(),
            BreakfastBowlTemplate(),
            StirFryTemplate(),
        ]

    def generate_top_meals(self, pantry: Pantry, limit: int = 3) -> List[MealRecommendation]:
        recommendations = [template.generate_recommendation(pantry) for template in self.templates]
        recommendations.sort(
            key=lambda recommendation: (
                recommendation.match_rate,
                recommendation.matched_slots,
                -recommendation.recipe.estimated_time_minutes,
                recommendation.recipe.name,
            ),
            reverse=True,
        )
        return recommendations[:limit]
