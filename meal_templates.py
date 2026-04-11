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
class PastaTemplate(MealTemplate):
    def requirements(self) -> List[TemplateRequirement]:
        return [
            TemplateRequirement(IngredientCategory.GRAIN, 1),
            TemplateRequirement(IngredientCategory.VEGETABLE, 2),
            TemplateRequirement(IngredientCategory.PROTEIN, 1),
        ]

    def build_recipe(self, selected_items: List[PantryItem]) -> Recipe:
        return Recipe(
            name="Simple Pasta Bowl",
            ingredients=self._recipe_ingredients_from_items(selected_items),
            steps=[
                "Cook the pasta until al dente.",
                "Cook the protein and saute the vegetables.",
                "Combine everything together and season to taste.",
            ],
            difficulty=Difficulty.EASY,
            estimated_time_minutes=25,
            meal_type=MealType.DINNER,
        )


class SoupTemplate(MealTemplate):
    def requirements(self) -> List[TemplateRequirement]:
        return [
            TemplateRequirement(IngredientCategory.VEGETABLE, 2),
            TemplateRequirement(IngredientCategory.PROTEIN, 1),
        ]

    def build_recipe(self, selected_items: List[PantryItem]) -> Recipe:
        return Recipe(
            name="Simple Soup",
            ingredients=self._recipe_ingredients_from_items(selected_items),
            steps=[
                "Chop and prep all ingredients.",
                "Simmer the vegetables and protein together in a pot until cooked through.",
                "Season and serve hot.",
            ],
            difficulty=Difficulty.EASY,
            estimated_time_minutes=30,
            meal_type=MealType.LUNCH,
        )


class YogurtParfaitTemplate(MealTemplate):
    def requirements(self) -> List[TemplateRequirement]:
        return [
            TemplateRequirement(IngredientCategory.DAIRY, 1),
            TemplateRequirement(IngredientCategory.FRUIT, 2),
            TemplateRequirement(IngredientCategory.GRAIN, 1),
        ]

    def build_recipe(self, selected_items: List[PantryItem]) -> Recipe:
        return Recipe(
            name="Simple Yogurt Parfait",
            ingredients=self._recipe_ingredients_from_items(selected_items),
            steps=[
                "Spoon the dairy base into a bowl or cup.",
                "Layer the fruit and grain on top.",
                "Serve immediately.",
            ],
            difficulty=Difficulty.EASY,
            estimated_time_minutes=5,
            meal_type=MealType.BREAKFAST,
        )


class SaladTemplate(MealTemplate):
    def requirements(self) -> List[TemplateRequirement]:
        return [
            TemplateRequirement(IngredientCategory.VEGETABLE, 2),
            TemplateRequirement(IngredientCategory.PROTEIN, 1),
            TemplateRequirement(IngredientCategory.FRUIT, 1),
        ]

    def build_recipe(self, selected_items: List[PantryItem]) -> Recipe:
        return Recipe(
            name="Simple Salad Bowl",
            ingredients=self._recipe_ingredients_from_items(selected_items),
            steps=[
                "Prep and chop all ingredients.",
                "Cook the protein if needed.",
                "Toss everything together and serve fresh.",
            ],
            difficulty=Difficulty.EASY,
            estimated_time_minutes=15,
            meal_type=MealType.LUNCH,
        )


class WrapTemplate(MealTemplate):
    def requirements(self) -> List[TemplateRequirement]:
        return [
            TemplateRequirement(IngredientCategory.GRAIN, 1),
            TemplateRequirement(IngredientCategory.PROTEIN, 1),
            TemplateRequirement(IngredientCategory.VEGETABLE, 2),
        ]

    def build_recipe(self, selected_items: List[PantryItem]) -> Recipe:
        return Recipe(
            name="Simple Wrap",
            ingredients=self._recipe_ingredients_from_items(selected_items),
            steps=[
                "Prepare the filling ingredients.",
                "Warm the grain base if needed.",
                "Assemble everything into a wrap and serve.",
            ],
            difficulty=Difficulty.EASY,
            estimated_time_minutes=15,
            meal_type=MealType.LUNCH,
        )


class SmoothieTemplate(MealTemplate):
    def requirements(self) -> List[TemplateRequirement]:
        return [
            TemplateRequirement(IngredientCategory.FRUIT, 2),
            TemplateRequirement(IngredientCategory.DAIRY, 1),
        ]

    def build_recipe(self, selected_items: List[PantryItem]) -> Recipe:
        return Recipe(
            name="Simple Smoothie",
            ingredients=self._recipe_ingredients_from_items(selected_items),
            steps=[
                "Add all ingredients to a blender.",
                "Blend until smooth.",
                "Pour into a glass and serve cold.",
            ],
            difficulty=Difficulty.EASY,
            estimated_time_minutes=5,
            meal_type=MealType.BREAKFAST,
        )


class RiceAndBeansTemplate(MealTemplate):
    def requirements(self) -> List[TemplateRequirement]:
        return [
            TemplateRequirement(IngredientCategory.GRAIN, 1),
            TemplateRequirement(IngredientCategory.PROTEIN, 1),
            TemplateRequirement(IngredientCategory.VEGETABLE, 1),
        ]

    def build_recipe(self, selected_items: List[PantryItem]) -> Recipe:
        return Recipe(
            name="Rice and Protein Bowl",
            ingredients=self._recipe_ingredients_from_items(selected_items),
            steps=[
                "Cook the grain until tender.",
                "Cook or warm the protein and vegetable.",
                "Serve everything together in a bowl.",
            ],
            difficulty=Difficulty.EASY,
            estimated_time_minutes=20,
            meal_type=MealType.DINNER,
        )


class SnackPlateTemplate(MealTemplate):
    def requirements(self) -> List[TemplateRequirement]:
        return [
            TemplateRequirement(IngredientCategory.PROTEIN, 1),
            TemplateRequirement(IngredientCategory.FRUIT, 1),
            TemplateRequirement(IngredientCategory.DAIRY, 1),
        ]

    def build_recipe(self, selected_items: List[PantryItem]) -> Recipe:
        return Recipe(
            name="Simple Snack Plate",
            ingredients=self._recipe_ingredients_from_items(selected_items),
            steps=[
                "Prep the ingredients if needed.",
                "Arrange everything on a plate or board.",
                "Serve immediately.",
            ],
            difficulty=Difficulty.EASY,
            estimated_time_minutes=5,
            meal_type=MealType.SNACK,
        )