import tkinter as tk
from threading import Thread
from tkinter import messagebox, ttk

from backend import IngredientCategory, MealGenerator, MealRecommendation, Pantry, PantryDatabase, Unit
from llm_generator import LocalLlamaRecipeGenerator


class What2EatGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("What2Eat")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        self.database = PantryDatabase("pantry.json")
        self.pantry = self.database.load_pantry()
        self.meal_generator = MealGenerator()
        self.ai_recipe_generator = LocalLlamaRecipeGenerator()
        self.generated_meals: list[MealRecommendation] = []
        self._generation_request_id = 0
        self.ai_status_var = tk.StringVar(value="AI status: checking...")
        self._ai_recipe_loading = False

        self._configure_styles()
        self._build_layout()
        self._refresh_pantry_table()
        self._refresh_ai_status()

    def _configure_styles(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Title.TLabel", font=("Arial", 22, "bold"))
        style.configure("Heading.TLabel", font=("Arial", 14, "bold"))
        style.configure("Card.TFrame", background="#f4f4f4", relief="flat")
        style.configure("Primary.TButton", font=("Arial", 11, "bold"), padding=10)
        style.configure("Secondary.TButton", font=("Arial", 10), padding=8)
        style.configure("AIStatusReady.TLabel", foreground="#1f6f43")
        style.configure("AIStatusUnavailable.TLabel", foreground="#9c2f2f")
        style.configure("AIStatusChecking.TLabel", foreground="#8a6d1d")

    def _build_layout(self) -> None:
        main = ttk.Frame(self.root, padding=16)
        main.pack(fill="both", expand=True)

        self._build_header(main)

        content = ttk.Frame(main)
        content.pack(fill="both", expand=True, pady=(12, 0))
        content.columnconfigure(0, weight=3)
        content.columnconfigure(1, weight=2)
        content.rowconfigure(0, weight=1)
        content.rowconfigure(1, weight=1)

        self._build_pantry_section(content)
        self._build_actions_section(content)
        self._build_results_section(content)
        self._build_recipe_preview_section(content)

    def _build_header(self, parent: ttk.Frame) -> None:
        header = ttk.Frame(parent)
        header.pack(fill="x")

        ttk.Label(header, text="What2Eat", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Track your pantry and generate meal ideas from what you already have.",
        ).pack(anchor="w", pady=(4, 0))
        self.ai_status_label = ttk.Label(
            header,
            textvariable=self.ai_status_var,
        )
        self.ai_status_label.pack(anchor="w", pady=(6, 0))

    def _build_pantry_section(self, parent: ttk.Frame) -> None:
        pantry_frame = ttk.LabelFrame(parent, text="Pantry", padding=12)
        pantry_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=(0, 10))
        pantry_frame.columnconfigure(0, weight=1)
        pantry_frame.rowconfigure(1, weight=1)

        input_row = ttk.Frame(pantry_frame)
        input_row.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        for i in range(5):
            input_row.columnconfigure(i, weight=1)

        ttk.Label(input_row, text="Ingredient").grid(row=0, column=0, sticky="w")
        ttk.Label(input_row, text="Quantity").grid(row=0, column=1, sticky="w")
        ttk.Label(input_row, text="Unit").grid(row=0, column=2, sticky="w")
        ttk.Label(input_row, text="Category").grid(row=0, column=3, sticky="w")

        self.ingredient_entry = ttk.Entry(input_row)
        self.ingredient_entry.grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=(4, 0))

        self.quantity_entry = ttk.Entry(input_row)
        self.quantity_entry.grid(row=1, column=1, sticky="ew", padx=(0, 8), pady=(4, 0))

        self.unit_combo = ttk.Combobox(
            input_row,
            values=["count", "g", "kg", "ml", "l", "cup", "tbsp", "tsp"],
            state="readonly",
        )
        self.unit_combo.grid(row=1, column=2, sticky="ew", padx=(0, 8), pady=(4, 0))
        self.unit_combo.set("count")

        self.category_combo = ttk.Combobox(
            input_row,
            values=[
                "vegetable",
                "protein",
                "grain",
                "dairy",
                "fruit",
                "spice",
                "fat",
                "sauce",
                "other",
            ],
            state="readonly",
        )
        self.category_combo.grid(row=1, column=3, sticky="ew", padx=(0, 8), pady=(4, 0))
        self.category_combo.set("vegetable")

        ttk.Button(input_row, text="Add Item", style="Primary.TButton", command=self._on_add_item).grid(
            row=1, column=4, sticky="ew", pady=(4, 0)
        )

        columns = ("ingredient", "quantity", "unit", "category")
        self.pantry_table = ttk.Treeview(pantry_frame, columns=columns, show="headings", height=12)
        self.pantry_table.grid(row=1, column=0, sticky="nsew")

        self.pantry_table.heading("ingredient", text="Ingredient")
        self.pantry_table.heading("quantity", text="Quantity")
        self.pantry_table.heading("unit", text="Unit")
        self.pantry_table.heading("category", text="Category")

        self.pantry_table.column("ingredient", width=180)
        self.pantry_table.column("quantity", width=90, anchor="center")
        self.pantry_table.column("unit", width=80, anchor="center")
        self.pantry_table.column("category", width=120, anchor="center")


        controls = ttk.Frame(pantry_frame)
        controls.grid(row=2, column=0, sticky="ew", pady=(10, 0))

        ttk.Button(controls, text="Edit Selected", style="Secondary.TButton").pack(side="left")
        ttk.Button(
            controls,
            text="Remove Selected",
            style="Secondary.TButton",
            command=self._on_remove_selected,
        ).pack(side="left", padx=8)
        ttk.Button(
            controls,
            text="Clear Pantry",
            style="Secondary.TButton",
            command=self._on_clear_pantry,
        ).pack(side="left")

    def _build_actions_section(self, parent: ttk.Frame) -> None:
        actions_frame = ttk.LabelFrame(parent, text="Meal Generation", padding=12)
        actions_frame.grid(row=0, column=1, sticky="nsew", pady=(0, 10))
        actions_frame.columnconfigure(0, weight=1)

        ttk.Label(actions_frame, text="Filters", style="Heading.TLabel").grid(row=0, column=0, sticky="w")

        ttk.Label(actions_frame, text="Meal Type").grid(row=1, column=0, sticky="w", pady=(10, 0))
        self.meal_type_combo = ttk.Combobox(
            actions_frame,
            values=["Any", "Breakfast", "Lunch", "Dinner", "Snack"],
            state="readonly",
        )
        self.meal_type_combo.grid(row=2, column=0, sticky="ew")
        self.meal_type_combo.set("Any")

        ttk.Label(actions_frame, text="Max Prep Time (minutes)").grid(row=3, column=0, sticky="w", pady=(10, 0))
        self.prep_time_entry = ttk.Entry(actions_frame)
        self.prep_time_entry.grid(row=4, column=0, sticky="ew")
        self.prep_time_entry.insert(0, "30")

        ttk.Label(actions_frame, text="Match Preference").grid(row=5, column=0, sticky="w", pady=(10, 0))
        self.match_combo = ttk.Combobox(
            actions_frame,
            values=["Exact matches first", "Flexible matches", "Fastest meals first"],
            state="readonly",
        )
        self.match_combo.grid(row=6, column=0, sticky="ew")
        self.match_combo.set("Flexible matches")

        ttk.Button(
            actions_frame,
            text="Generate Meals",
            style="Primary.TButton",
            command=self._on_generate_meals,
        ).grid(row=7, column=0, sticky="ew", pady=(18, 8))
        ttk.Button(actions_frame, text="Save Pantry", style="Secondary.TButton", command=self._on_save_pantry).grid(
            row=8, column=0, sticky="ew", pady=(0, 8)
        )
        ttk.Button(actions_frame, text="Load Pantry", style="Secondary.TButton", command=self._on_load_pantry).grid(
            row=9, column=0, sticky="ew"
        )

    def _build_results_section(self, parent: ttk.Frame) -> None:
        results_frame = ttk.LabelFrame(parent, text="Generated Meals", padding=12)
        results_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)

        self.results_list = tk.Listbox(results_frame, height=10)
        self.results_list.grid(row=0, column=0, sticky="nsew")
        self.results_list.bind("<<ListboxSelect>>", self._on_select_generated_meal)


    def _build_recipe_preview_section(self, parent: ttk.Frame) -> None:
        preview_frame = ttk.LabelFrame(parent, text="Recipe Preview", padding=12)
        preview_frame.grid(row=1, column=1, sticky="nsew")
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(1, weight=1)

        ttk.Label(preview_frame, text="Selected Meal", style="Heading.TLabel").grid(
            row=0, column=0, sticky="w"
        )

        self.preview_text = tk.Text(preview_frame, wrap="word", height=14)
        self.preview_text.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        self.preview_text.configure(state="disabled")

    def _on_add_item(self) -> None:
        name = self.ingredient_entry.get().strip()
        if not name:
            messagebox.showerror("Missing Ingredient", "Please enter an ingredient name.")
            return

        try:
            quantity = float(self.quantity_entry.get().strip())
            if quantity <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Quantity", "Quantity must be a positive number.")
            return

        unit = Unit(self.unit_combo.get())
        category = IngredientCategory(self.category_combo.get())

        self.database.add_ingredient(
            pantry=self.pantry,
            name=name,
            quantity=quantity,
            unit=unit,
            category=category,
        )
        self._refresh_pantry_table()
        self.ingredient_entry.delete(0, tk.END)
        self.quantity_entry.delete(0, tk.END)

    def _on_remove_selected(self) -> None:
        selected_ids = self.pantry_table.selection()
        if not selected_ids:
            messagebox.showinfo("No Selection", "Select a pantry item to remove.")
            return

        selected_item = self.pantry_table.item(selected_ids[0])
        ingredient_name = str(selected_item["values"][0])
        self.pantry.remove_item(ingredient_name)
        self.database.save_pantry(self.pantry)
        self._refresh_pantry_table()

    def _on_clear_pantry(self) -> None:
        self.pantry = Pantry()
        self.database.save_pantry(self.pantry)
        self._refresh_pantry_table()

    def _on_save_pantry(self) -> None:
        self.database.save_pantry(self.pantry)
        messagebox.showinfo("Pantry Saved", "Pantry saved to pantry.json.")

    def _on_load_pantry(self) -> None:
        self.pantry = self.database.load_pantry()
        self._refresh_pantry_table()
        messagebox.showinfo("Pantry Loaded", "Pantry loaded from pantry.json.")

    def _on_generate_meals(self) -> None:
        max_prep_time = self._parse_max_prep_time()
        if max_prep_time is None:
            return

        meal_type = self.meal_type_combo.get()
        self._generation_request_id += 1
        request_id = self._generation_request_id
        self.generated_meals = self.meal_generator.generate_top_meals(
            self.pantry,
            limit=3,
            meal_type=meal_type,
            max_prep_time_minutes=max_prep_time,
        )
        self._ai_recipe_loading = True
        self._refresh_generated_meals_list()

        if not self.generated_meals:
            self._set_preview_text("Loading Specialized Recipe...")
        else:
            self.results_list.selection_clear(0, tk.END)
            self.results_list.selection_set(0)
            self._set_preview_text("Loading Specialized Recipe...")

        self._start_ai_recipe_generation(
            request_id,
            meal_type=meal_type,
            max_prep_time_minutes=max_prep_time,
        )

    def _on_select_generated_meal(self, event: tk.Event) -> None:
        selection = self.results_list.curselection()
        if not selection:
            return

        selected_index = selection[0]
        if self._ai_recipe_loading:
            if selected_index == 0:
                self._set_preview_text("Loading Specialized Recipe...")
                return
            selected_index -= 1

        if selected_index >= len(self.generated_meals):
            return

        self._show_meal_preview(self.generated_meals[selected_index])

    def _show_meal_preview(self, recommendation: MealRecommendation) -> None:
        recipe = recommendation.recipe
        ingredient_names = [ingredient.ingredient_name for ingredient in recipe.ingredients]
        ingredient_text = ", ".join(ingredient_names) if ingredient_names else "No pantry matches yet."
        missing_text = ", ".join(category.value for category in recommendation.missing_categories) or "None"
        steps_text = "\n".join(f"{index}. {step}" for index, step in enumerate(recipe.steps, start=1))
        source_text = "AI-generated top pick" if recommendation.is_ai_generated else "Template recommendation"

        preview = (
            f"{recipe.name}\n\n"
            f"Source: {source_text}\n"
            f"Match: {recommendation.matched_slots}/{recommendation.total_slots} "
            f"({recommendation.match_rate:.0%})\n"
            f"Ingredients used: {ingredient_text}\n"
            f"Missing categories: {missing_text}\n\n"
            f"Steps:\n{steps_text}"
        )
        self._set_preview_text(preview)

    def _set_preview_text(self, content: str) -> None:
        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert("1.0", content)
        self.preview_text.configure(state="disabled")

    def _refresh_pantry_table(self) -> None:
        for item_id in self.pantry_table.get_children():
            self.pantry_table.delete(item_id)

        for pantry_item in sorted(self.pantry.list_items(), key=lambda item: item.ingredient.name.lower()):
            self.pantry_table.insert(
                "",
                "end",
                values=(
                    pantry_item.ingredient.name,
                    pantry_item.quantity,
                    pantry_item.unit.value,
                    pantry_item.ingredient.category.value,
                ),
            )

    def _start_ai_recipe_generation(
        self,
        request_id: int,
        meal_type: str,
        max_prep_time_minutes: int | None,
    ) -> None:
        worker = Thread(
            target=self._generate_ai_recipe_worker,
            args=(request_id, meal_type, max_prep_time_minutes),
            daemon=True,
        )
        worker.start()

    def _generate_ai_recipe_worker(
        self,
        request_id: int,
        meal_type: str,
        max_prep_time_minutes: int | None,
    ) -> None:
        recommendation = self.ai_recipe_generator.generate_recipe(
            self.pantry,
            meal_type=meal_type,
            max_prep_time_minutes=max_prep_time_minutes,
        )
        self.root.after(0, lambda: self._apply_ai_recipe_result(request_id, recommendation))

    def _apply_ai_recipe_result(
        self,
        request_id: int,
        recommendation: MealRecommendation | None,
    ) -> None:
        if request_id != self._generation_request_id or recommendation is None:
            if request_id == self._generation_request_id:
                self._ai_recipe_loading = False
                self._refresh_generated_meals_list()
                if self.generated_meals:
                    self.results_list.selection_clear(0, tk.END)
                    self.results_list.selection_set(0)
                    self._show_meal_preview(self.generated_meals[0])
            return

        self._ai_recipe_loading = False
        self.generated_meals = [
            meal for meal in self.generated_meals if not meal.is_ai_generated
        ]
        self.generated_meals.insert(0, recommendation)
        self._refresh_generated_meals_list()
        self.results_list.selection_clear(0, tk.END)
        self.results_list.selection_set(0)
        self._show_meal_preview(recommendation)

    def _refresh_generated_meals_list(self) -> None:
        self.results_list.delete(0, tk.END)

        if self._ai_recipe_loading:
            self.results_list.insert(tk.END, "Loading Specialized Recipe...")
            self.results_list.itemconfig(
                0,
                bg="#e8f0ff",
                fg="#22406a",
                selectbackground="#9eb9e8",
                selectforeground="#10233d",
            )

        for recommendation in self.generated_meals:
            label_prefix = "Specialized Meal: " if recommendation.is_ai_generated else ""
            self.results_list.insert(
                tk.END,
                f"{label_prefix}{recommendation.recipe.name} ({recommendation.match_rate:.0%} match)",
            )
            row_index = self.results_list.size() - 1
            if recommendation.is_ai_generated:
                self.results_list.itemconfig(
                    row_index,
                    bg="#fff1bf",
                    fg="#5c4300",
                    selectbackground="#f0c24b",
                    selectforeground="#2c2100",
                )

    def _refresh_ai_status(self) -> None:
        status_text = self.ai_recipe_generator.get_status()
        self.ai_status_var.set(status_text)

        if status_text.startswith("AI ready:"):
            self.ai_status_label.configure(style="AIStatusReady.TLabel")
        elif status_text.startswith("AI unavailable:"):
            self.ai_status_label.configure(style="AIStatusUnavailable.TLabel")
        else:
            self.ai_status_label.configure(style="AIStatusChecking.TLabel")

    def _parse_max_prep_time(self) -> int | None:
        raw_value = self.prep_time_entry.get().strip()
        if not raw_value:
            return None

        try:
            parsed = int(raw_value)
        except ValueError:
            messagebox.showerror("Invalid Prep Time", "Max prep time must be a whole number.")
            return None

        if parsed <= 0:
            messagebox.showerror("Invalid Prep Time", "Max prep time must be greater than zero.")
            return None

        return parsed

if __name__ == "__main__":
    root = tk.Tk()
    app = What2EatGUI(root)
    root.mainloop()
