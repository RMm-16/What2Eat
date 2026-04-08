from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend import Difficulty, Pantry, Recipe, RecipeIngredient
from meal_templates import MealRecommendation

try:
    from llama_cpp import Llama
except ImportError:
    Llama = None


@dataclass(frozen=True)
class LocalLlamaConfig:
    model_path: Path = Path("models/smollm2-1.7b-instruct-q4.gguf")
    n_ctx: int = 2048
    temperature: float = 0.4
    max_tokens: int = 400
    n_threads: Optional[int] = None


class LocalLlamaRecipeGenerator:
    def __init__(self, config: Optional[LocalLlamaConfig] = None) -> None:
        self.config = config or LocalLlamaConfig()
        self._client: Any = None

    def generate_recipe(self, pantry: Pantry) -> Optional[MealRecommendation]:
        if not pantry.list_items():
            return None

        client = self._get_client()
        if client is None:
            return None

        try:
            response = client.create_chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You generate one simple recipe using only pantry ingredients. "
                            "Return valid JSON only."
                        ),
                    },
                    {
                        "role": "user",
                        "content": self._build_prompt(pantry),
                    },
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                response_format={"type": "json_object"},
            )
        except Exception:
            return None

        raw_response = self._extract_text(response)
        recipe_payload = self._parse_response(raw_response)
        if recipe_payload is None:
            return None

        return self._build_recommendation(recipe_payload, pantry)

    def is_available(self) -> bool:
        return self._get_client() is not None

    def get_status(self) -> str:
        if Llama is None:
            return "AI unavailable: llama-cpp-python is not installed for this Python environment."

        model_path = self._resolve_model_path()
        if model_path is None:
            return "AI unavailable: no GGUF model was found in the models folder."

        client = self._get_client()
        if client is None:
            return f"AI unavailable: failed to load model at {model_path.name}."

        return f"AI ready: {model_path.name}"

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client

        if Llama is None:
            return None

        model_path = self._resolve_model_path()

        if model_path is None or not model_path.exists():
            return None

        try:
            self._client = Llama(
                model_path=str(model_path),
                n_ctx=self.config.n_ctx,
                n_threads=self.config.n_threads,
                verbose=False,
                chat_format="chatml",
            )
        except Exception:
            self._client = None

        return self._client

    def _resolve_model_path(self) -> Optional[Path]:
        model_path = self.config.model_path
        if not model_path.is_absolute():
            model_path = Path(__file__).resolve().parent / model_path

        if model_path.exists():
            return model_path

        models_dir = Path(__file__).resolve().parent / "models"
        if not models_dir.exists():
            return None

        preferred_matches = sorted(models_dir.glob("smollm2*.gguf"))
        if preferred_matches:
            return preferred_matches[0]

        any_matches = sorted(models_dir.glob("*.gguf"))
        if len(any_matches) == 1:
            return any_matches[0]

        return None

    def _build_prompt(self, pantry: Pantry) -> str:
        pantry_lines = []
        for item in sorted(pantry.list_items(), key=lambda pantry_item: pantry_item.ingredient.name.lower()):
            pantry_lines.append(
                f"- {item.ingredient.name} ({item.quantity:g} {item.unit.value}, "
                f"{item.ingredient.category.value})"
            )

        pantry_text = "\n".join(pantry_lines)

        return (
            "Create one practical home recipe from this pantry.\n"
            "Use only ingredient names that appear exactly in the pantry list.\n"
            "Do not invent ingredients.\n"
            "Choose between 2 and 6 pantry ingredients.\n"
            "Return JSON only with this exact shape:\n"
            "{\n"
            '  "name": "Recipe name",\n'
            '  "ingredients": ["Ingredient 1", "Ingredient 2"],\n'
            '  "steps": ["Step 1", "Step 2", "Step 3"],\n'
            '  "difficulty": "easy",\n'
            '  "estimated_time_minutes": 25\n'
            "}\n"
            "Rules:\n"
            "- ingredients must exactly match pantry names\n"
            "- steps must be concise and realistic\n"
            "- difficulty must be one of: easy, medium, hard\n"
            "- estimated_time_minutes must be an integer\n"
            "Pantry:\n"
            f"{pantry_text}\n"
        )

    def _extract_text(self, response: Any) -> str:
        try:
            choices = response.get("choices", [])
            first_choice = choices[0]
            message = first_choice.get("message", {})
            return str(message.get("content", "")).strip()
        except (AttributeError, IndexError, TypeError):
            return ""

    def _parse_response(self, raw_response: str) -> Optional[Dict[str, Any]]:
        if not raw_response:
            return None

        try:
            parsed = json.loads(raw_response)
        except json.JSONDecodeError:
            return None

        if not isinstance(parsed, dict):
            return None

        return parsed

    def _build_recommendation(
        self,
        recipe_payload: Dict[str, Any],
        pantry: Pantry,
    ) -> Optional[MealRecommendation]:
        recipe_name = str(recipe_payload.get("name", "")).strip()
        if not recipe_name:
            return None

        raw_ingredient_names = recipe_payload.get("ingredients")
        if not isinstance(raw_ingredient_names, list):
            return None

        selected_ingredients: List[RecipeIngredient] = []
        requested_count = 0
        for value in raw_ingredient_names:
            ingredient_name = str(value).strip()
            if not ingredient_name:
                continue

            requested_count += 1
            pantry_item = pantry.get_item(ingredient_name)
            if pantry_item is None:
                continue

            selected_ingredients.append(
                RecipeIngredient(
                    ingredient_name=pantry_item.ingredient.name,
                    quantity=pantry_item.quantity,
                    unit=pantry_item.unit,
                )
            )

        if not selected_ingredients:
            return None

        raw_steps = recipe_payload.get("steps")
        if not isinstance(raw_steps, list):
            return None

        steps = [str(step).strip() for step in raw_steps if str(step).strip()]
        if not steps:
            return None

        difficulty = self._parse_difficulty(recipe_payload.get("difficulty"))
        estimated_time_minutes = self._parse_estimated_time(recipe_payload.get("estimated_time_minutes"))
        total_slots = max(requested_count, len(selected_ingredients))
        matched_slots = len(selected_ingredients)

        recipe = Recipe(
            name=recipe_name,
            ingredients=selected_ingredients,
            steps=steps,
            difficulty=difficulty,
            estimated_time_minutes=estimated_time_minutes,
        )
        return MealRecommendation(
            recipe=recipe,
            match_rate=matched_slots / total_slots if total_slots else 0.0,
            matched_slots=matched_slots,
            total_slots=total_slots,
            missing_categories=[],
            is_ai_generated=True,
        )

    def _parse_difficulty(self, value: Any) -> Difficulty:
        normalized = str(value).strip().lower()
        for difficulty in Difficulty:
            if difficulty.value == normalized:
                return difficulty
        return Difficulty.EASY

    def _parse_estimated_time(self, value: Any) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return 20

        return max(parsed, 5)
