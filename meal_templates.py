from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import List

from backend import (
    Difficulty,
    IngredientCategory,
    MealType,
    Pantry,
    PantryItem,
    Recipe,
    RecipeIngredient,
)


@dataclass(frozen=True)
class TemplateRequirement:
    category: IngredientCategory
    count: int


@dataclass
class MealRecommendation:
    recipe: Recipe
    match_rate: float
    matched_slots: int
    total_slots: int
    missing_categories: List[IngredientCategory]
    is_ai_generated: bool = False


class MealTemplate(ABC):
    def generate_recommendation(self, pantry: Pantry) -> MealRecommendation:
        selected_items: List[PantryItem] = []
        missing_categories: List[IngredientCategory] = []
        matched_slots = 0
        total_slots = sum(requirement.count for requirement in self.requirements())

        pantry_items = pantry.list_items()

        for requirement in self.requirements():
            category_matches = [
                item for item in pantry_items if item.ingredient.category == requirement.category
            ]
            category_matches.sort(key=lambda item: item.ingredient.name.lower())

            selected = category_matches[: requirement.count]
            selected_items.extend(selected)
            matched_slots += len(selected)

            missing_count = requirement.count - len(selected)
            if missing_count > 0:
                missing_categories.extend([requirement.category] * missing_count)

        recipe = self.build_recipe(selected_items)
        match_rate = matched_slots / total_slots if total_slots else 0.0

        return MealRecommendation(
            recipe=recipe,
            match_rate=match_rate,
            matched_slots=matched_slots,
            total_slots=total_slots,
            missing_categories=missing_categories,
        )

    def _recipe_ingredients_from_items(self, pantry_items: List[PantryItem]) -> List[RecipeIngredient]:
        return [
            RecipeIngredient(
                ingredient_name=pantry_item.ingredient.name,
                quantity=pantry_item.quantity,
                unit=pantry_item.unit,
            )
            for pantry_item in pantry_items
        ]

    def _format_template_name(self) -> str:
        parts = [f"{requirement.count} {requirement.category.value}" for requirement in self.requirements()]
        return " + ".join(parts)

    def _default_steps(self) -> List[str]:
        return [
            "Prep the selected ingredients.",
            "Cook each ingredient using your preferred method.",
            "Combine everything into a simple meal and season to taste.",
        ]

    def requirements(self) -> List[TemplateRequirement]:
        raise NotImplementedError

    def build_recipe(self, selected_items: List[PantryItem]) -> Recipe:
        raise NotImplementedError


class GrainVegBowlTemplate(MealTemplate):
    def requirements(self) -> List[TemplateRequirement]:
        return [
            TemplateRequirement(IngredientCategory.GRAIN, 2),
            TemplateRequirement(IngredientCategory.VEGETABLE, 1),
        ]

    def build_recipe(self, selected_items: List[PantryItem]) -> Recipe:
        return Recipe(
            name="Simple Vegetable Bowl",
            ingredients=self._recipe_ingredients_from_items(selected_items),
            steps=[
                "Cook the grains until tender.",
                "Saute or roast the vegetable.",
                "Layer the grains and vegetable together in a bowl.",
            ],
            difficulty=Difficulty.EASY,
            estimated_time_minutes=20,
            meal_type=MealType.LUNCH,
        )


class ProteinPlateTemplate(MealTemplate):
    def requirements(self) -> List[TemplateRequirement]:
        return [
            TemplateRequirement(IngredientCategory.PROTEIN, 1),
            TemplateRequirement(IngredientCategory.VEGETABLE, 2),
        ]

    def build_recipe(self, selected_items: List[PantryItem]) -> Recipe:
        return Recipe(
            name="Simple Protein Plate",
            ingredients=self._recipe_ingredients_from_items(selected_items),
            steps=[
                "Cook the protein until done.",
                "Prepare the vegetables as a side.",
                "Serve the protein with the vegetables on one plate.",
            ],
            difficulty=Difficulty.EASY,
            estimated_time_minutes=30,
            meal_type=MealType.DINNER,
        )


class BreakfastBowlTemplate(MealTemplate):
    def requirements(self) -> List[TemplateRequirement]:
        return [
            TemplateRequirement(IngredientCategory.GRAIN, 1),
            TemplateRequirement(IngredientCategory.FRUIT, 1),
            TemplateRequirement(IngredientCategory.DAIRY, 1),
        ]

    def build_recipe(self, selected_items: List[PantryItem]) -> Recipe:
        return Recipe(
            name="Quick Breakfast Bowl",
            ingredients=self._recipe_ingredients_from_items(selected_items),
            steps=[
                "Prepare the grain base.",
                "Add the fruit and dairy on top.",
                "Mix together and serve right away.",
            ],
            difficulty=Difficulty.EASY,
            estimated_time_minutes=10,
            meal_type=MealType.BREAKFAST,
        )


class StirFryTemplate(MealTemplate):
    def requirements(self) -> List[TemplateRequirement]:
        return [
            TemplateRequirement(IngredientCategory.PROTEIN, 2),
            TemplateRequirement(IngredientCategory.VEGETABLE, 2),
            TemplateRequirement(IngredientCategory.FRUIT, 1),
        ]

    def build_recipe(self, selected_items: List[PantryItem]) -> Recipe:
        return Recipe(
            name="Basic Stir Fry",
            ingredients=self._recipe_ingredients_from_items(selected_items),
            steps=[
                "Cook the protein in a hot pan.",
                "Add the vegetables and stir-fry until tender-crisp.",
                "Finish with the sauce and toss everything together.",
            ],
            difficulty=Difficulty.MEDIUM,
            estimated_time_minutes=35,
            meal_type=MealType.DINNER,
        )
