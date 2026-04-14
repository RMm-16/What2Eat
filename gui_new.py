import tkinter as tk
from threading import Thread
from tkinter import messagebox, ttk

from backend import IngredientCategory, MealGenerator, MealRecommendation, Pantry, PantryDatabase, Unit
from llm_generator import LocalLlamaRecipeGenerator


class What2EatCleanGUI:
    MAX_RECIPE_OUTPUTS = 6

    BACKGROUND = "#f5f1ea"
    SURFACE = "#fffdf8"
    SURFACE_ALT = "#f0e7db"
    BORDER = "#d8c9b6"
    TEXT = "#2d241d"
    MUTED = "#6e6256"
    ACCENT = "#2f7a5f"
    ACCENT_SOFT = "#d9ede4"
    WARNING = "#a65d2c"
    WARNING_SOFT = "#f8e2d3"
    INFO = "#30536e"
    INFO_SOFT = "#dbe9f4"

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("What2Eat")
        self.root.geometry("1240x820")
        self.root.minsize(1024, 700)
        self.root.configure(bg=self.BACKGROUND)

        self.database = PantryDatabase("pantry.json")
        self.pantry = self.database.load_pantry()
        self.meal_generator = MealGenerator()
        self.ai_recipe_generator = LocalLlamaRecipeGenerator()
        self.generated_meals: list[MealRecommendation] = []
        self._generation_request_id = 0
        self._ai_recipe_loading = False
        self._selected_pantry_item_name: str | None = None

        self.ai_status_var = tk.StringVar(value="Checking local AI model...")
        self.summary_items_var = tk.StringVar()
        self.summary_categories_var = tk.StringVar()
        self.summary_meals_var = tk.StringVar(value="No meals generated yet")
        self.selection_hint_var = tk.StringVar(value="Select a meal to see recipe details.")

        self._configure_styles()
        self._build_layout()
        self._refresh_pantry_table()
        self._refresh_summary_cards()
        self._refresh_ai_status()

    def _configure_styles(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")

        self.root.option_add("*Font", "Helvetica 11")

        style.configure(".", background=self.BACKGROUND, foreground=self.TEXT)
        style.configure("Root.TFrame", background=self.BACKGROUND)
        style.configure("Panel.TFrame", background=self.SURFACE, relief="flat")
        style.configure("SoftPanel.TFrame", background=self.SURFACE_ALT, relief="flat")
        style.configure("Card.TFrame", background=self.SURFACE, relief="flat")
        style.configure("AccentCard.TFrame", background=self.ACCENT_SOFT, relief="flat")
        style.configure("InfoCard.TFrame", background=self.INFO_SOFT, relief="flat")
        style.configure("WarningCard.TFrame", background=self.WARNING_SOFT, relief="flat")

        style.configure("Hero.TLabel", font=("Georgia", 28, "bold"), background=self.BACKGROUND, foreground=self.TEXT)
        style.configure("Subtitle.TLabel", font=("Helvetica", 12), background=self.BACKGROUND, foreground=self.MUTED)
        style.configure("Section.TLabel", font=("Georgia", 16, "bold"), background=self.SURFACE, foreground=self.TEXT)
        style.configure("CardValue.TLabel", font=("Georgia", 20, "bold"), foreground=self.TEXT)
        style.configure("CardLabel.TLabel", font=("Helvetica", 10), foreground=self.MUTED)
        style.configure("AccentCardValue.TLabel", font=("Georgia", 20, "bold"), background=self.ACCENT_SOFT, foreground=self.TEXT)
        style.configure("InfoCardValue.TLabel", font=("Georgia", 20, "bold"), background=self.INFO_SOFT, foreground=self.TEXT)
        style.configure("WarningCardValue.TLabel", font=("Georgia", 20, "bold"), background=self.WARNING_SOFT, foreground=self.TEXT)
        style.configure("AccentCardLabel.TLabel", font=("Helvetica", 10), background=self.ACCENT_SOFT, foreground=self.MUTED)
        style.configure("InfoCardLabel.TLabel", font=("Helvetica", 10), background=self.INFO_SOFT, foreground=self.MUTED)
        style.configure("WarningCardLabel.TLabel", font=("Helvetica", 10), background=self.WARNING_SOFT, foreground=self.MUTED)
        style.configure("PanelText.TLabel", background=self.SURFACE, foreground=self.TEXT)
        style.configure("Muted.TLabel", background=self.SURFACE, foreground=self.MUTED)
        style.configure("StatusReady.TLabel", background=self.SURFACE_ALT, foreground=self.ACCENT, font=("Helvetica", 10, "bold"))
        style.configure("StatusBusy.TLabel", background=self.SURFACE_ALT, foreground=self.WARNING, font=("Helvetica", 10, "bold"))
        style.configure("StatusOff.TLabel", background=self.SURFACE_ALT, foreground="#8c3d3d", font=("Helvetica", 10, "bold"))

        style.configure(
            "Primary.TButton",
            font=("Helvetica", 11, "bold"),
            padding=(14, 10),
            background=self.ACCENT,
            foreground="#ffffff",
            borderwidth=0,
        )
        style.map("Primary.TButton", background=[("active", "#25634d"), ("pressed", "#1f5541")])

        style.configure(
            "Secondary.TButton",
            font=("Helvetica", 10),
            padding=(12, 8),
            background=self.SURFACE_ALT,
            foreground=self.TEXT,
            bordercolor=self.BORDER,
            borderwidth=1,
        )
        style.map("Secondary.TButton", background=[("active", "#e7dccd")])

        style.configure(
            "Filter.TCombobox",
            fieldbackground="#ffffff",
            background="#ffffff",
            foreground=self.TEXT,
            padding=6,
        )
        style.configure("Clean.Treeview", background="#fffdfb", fieldbackground="#fffdfb", foreground=self.TEXT, rowheight=28)
        style.configure("Clean.Treeview.Heading", background=self.SURFACE_ALT, foreground=self.TEXT, font=("Helvetica", 10, "bold"))

    def _build_layout(self) -> None:
        main = ttk.Frame(self.root, style="Root.TFrame", padding=22)
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=5)
        main.columnconfigure(1, weight=4)
        main.rowconfigure(2, weight=1)

        self._build_header(main)
        self._build_summary_row(main)
        self._build_content(main)

    def _build_header(self, parent: ttk.Frame) -> None:
        header = ttk.Frame(parent, style="Root.TFrame")
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text="What2Eat", style="Hero.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text="A calmer pantry dashboard for tracking ingredients and turning them into realistic meal ideas.",
            style="Subtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        status_shell = ttk.Frame(header, style="SoftPanel.TFrame", padding=(12, 10))
        status_shell.grid(row=0, column=1, rowspan=2, sticky="e")
        self.ai_status_label = ttk.Label(status_shell, textvariable=self.ai_status_var, style="StatusBusy.TLabel")
        self.ai_status_label.pack()

    def _build_summary_row(self, parent: ttk.Frame) -> None:
        summary = ttk.Frame(parent, style="Root.TFrame")
        summary.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(18, 18))
        for column in range(3):
            summary.columnconfigure(column, weight=1)

        self._create_stat_card(summary, 0, "Pantry Items", self.summary_items_var, "AccentCard.TFrame")
        self._create_stat_card(summary, 1, "Categories", self.summary_categories_var, "InfoCard.TFrame")
        self._create_stat_card(summary, 2, "Meal Feed", self.summary_meals_var, "WarningCard.TFrame")

    def _create_stat_card(
        self,
        parent: ttk.Frame,
        column: int,
        label: str,
        value_var: tk.StringVar,
        frame_style: str,
    ) -> None:
        card = ttk.Frame(parent, style=frame_style, padding=16)
        card.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 8, 0))
        style_prefix = frame_style.split(".")[0]
        ttk.Label(card, text=label, style=f"{style_prefix}Label.TLabel").pack(anchor="w")
        value = ttk.Label(card, textvariable=value_var, style=f"{style_prefix}Value.TLabel")
        value.pack(anchor="w", pady=(6, 0))

    def _build_content(self, parent: ttk.Frame) -> None:
        left_panel = ttk.Frame(parent, style="Panel.TFrame", padding=18)
        left_panel.grid(row=2, column=0, sticky="nsew", padx=(0, 12))
        left_panel.columnconfigure(0, weight=1)
        left_panel.rowconfigure(4, weight=1)

        right_panel = ttk.Frame(parent, style="Panel.TFrame", padding=18)
        right_panel.grid(row=2, column=1, sticky="nsew")
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(1, weight=1)
        right_panel.rowconfigure(2, weight=1)

        studio_panel = ttk.Frame(right_panel, style="Panel.TFrame")
        studio_panel.grid(row=0, column=0, sticky="ew")
        studio_panel.columnconfigure(0, weight=1)

        results_panel = ttk.Frame(right_panel, style="Panel.TFrame")
        results_panel.grid(row=1, column=0, sticky="nsew", pady=(18, 0))
        results_panel.columnconfigure(0, weight=1)
        results_panel.rowconfigure(0, weight=1)

        preview_panel = ttk.Frame(right_panel, style="Panel.TFrame")
        preview_panel.grid(row=2, column=0, sticky="nsew", pady=(18, 0))
        preview_panel.columnconfigure(0, weight=1)
        preview_panel.rowconfigure(0, weight=1)

        self._build_pantry_form(left_panel)
        self._build_pantry_toolbar(left_panel)
        self._build_pantry_table(left_panel)
        self._build_generation_controls(studio_panel)
        self._build_results_list(results_panel)
        self._build_recipe_preview(preview_panel)

    def _build_pantry_form(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="Pantry", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            parent,
            text="Add or update ingredients with cleaner controls and a quick overview of what is on hand.",
            style="Muted.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 14))

        form = ttk.Frame(parent, style="Panel.TFrame")
        form.grid(row=2, column=0, sticky="ew")
        for column in range(5):
            form.columnconfigure(column, weight=1)

        ttk.Label(form, text="Ingredient", style="PanelText.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(form, text="Quantity", style="PanelText.TLabel").grid(row=0, column=1, sticky="w")
        ttk.Label(form, text="Unit", style="PanelText.TLabel").grid(row=0, column=2, sticky="w")
        ttk.Label(form, text="Category", style="PanelText.TLabel").grid(row=0, column=3, sticky="w")

        self.ingredient_entry = ttk.Entry(form)
        self.ingredient_entry.grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=(6, 0))

        self.quantity_entry = ttk.Entry(form)
        self.quantity_entry.grid(row=1, column=1, sticky="ew", padx=(0, 8), pady=(6, 0))

        self.unit_combo = ttk.Combobox(
            form,
            state="readonly",
            style="Filter.TCombobox",
            values=[unit.value for unit in Unit],
        )
        self.unit_combo.grid(row=1, column=2, sticky="ew", padx=(0, 8), pady=(6, 0))
        self.unit_combo.set(Unit.COUNT.value)

        self.category_combo = ttk.Combobox(
            form,
            state="readonly",
            style="Filter.TCombobox",
            values=[category.value for category in IngredientCategory],
        )
        self.category_combo.grid(row=1, column=3, sticky="ew", padx=(0, 8), pady=(6, 0))
        self.category_combo.set(IngredientCategory.VEGETABLE.value)

        add_button = ttk.Button(form, text="Add Item", style="Primary.TButton", command=self._on_add_item)
        add_button.grid(row=1, column=4, sticky="ew", pady=(6, 0))

    def _build_pantry_toolbar(self, parent: ttk.Frame) -> None:
        toolbar = ttk.Frame(parent, style="Panel.TFrame")
        toolbar.grid(row=3, column=0, sticky="ew", pady=(18, 12))
        toolbar.columnconfigure(0, weight=1)

        ttk.Label(
            toolbar,
            text="Select a row to edit or remove it. Pantry changes save automatically.",
            style="Muted.TLabel",
        ).grid(row=0, column=0, sticky="w")

        actions = ttk.Frame(toolbar, style="Panel.TFrame")
        actions.grid(row=1, column=0, sticky="w", pady=(10, 0))
        ttk.Button(actions, text="Edit Selected", style="Secondary.TButton", command=self._on_edit_selected).pack(side="left")
        ttk.Button(actions, text="Remove Selected", style="Secondary.TButton", command=self._on_remove_selected).pack(side="left", padx=8)
        ttk.Button(actions, text="Clear Pantry", style="Secondary.TButton", command=self._on_clear_pantry).pack(side="left")

    def _build_pantry_table(self, parent: ttk.Frame) -> None:
        table_shell = ttk.Frame(parent, style="Panel.TFrame")
        table_shell.grid(row=4, column=0, sticky="nsew")
        table_shell.columnconfigure(0, weight=1)
        table_shell.rowconfigure(0, weight=1)

        columns = ("ingredient", "quantity", "unit", "category")
        self.pantry_table = ttk.Treeview(table_shell, columns=columns, show="headings", style="Clean.Treeview")
        self.pantry_table.grid(row=0, column=0, sticky="nsew")
        self.pantry_table.bind("<<TreeviewSelect>>", self._on_select_pantry_item)

        scrollbar = ttk.Scrollbar(table_shell, orient="vertical", command=self.pantry_table.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.pantry_table.configure(yscrollcommand=scrollbar.set)

        headings = {
            "ingredient": ("Ingredient", 220, "w"),
            "quantity": ("Qty", 80, "center"),
            "unit": ("Unit", 80, "center"),
            "category": ("Category", 120, "center"),
        }
        for column, (label, width, anchor) in headings.items():
            self.pantry_table.heading(column, text=label)
            self.pantry_table.column(column, width=width, anchor=anchor)

    def _build_generation_controls(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        ttk.Label(parent, text="Meal Studio", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            parent,
            text="Filter the meal feed, then open a recipe card for the full breakdown.",
            style="Muted.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        filter_box = ttk.Frame(parent, style="SoftPanel.TFrame", padding=14)
        filter_box.grid(row=2, column=0, sticky="ew", pady=(14, 16))
        filter_box.columnconfigure(0, weight=1)
        filter_box.columnconfigure(1, weight=1)
        filter_box.columnconfigure(2, weight=1)

        ttk.Label(filter_box, text="Meal Type", style="PanelText.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(filter_box, text="Max Prep Time (minutes)", style="PanelText.TLabel").grid(row=0, column=1, sticky="w")
        ttk.Label(filter_box, text="Match Preference", style="PanelText.TLabel").grid(row=0, column=2, sticky="w")

        self.meal_type_combo = ttk.Combobox(
            filter_box,
            state="readonly",
            style="Filter.TCombobox",
            values=["Any", "Breakfast", "Lunch", "Dinner", "Snack"],
        )
        self.meal_type_combo.grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=(6, 0))
        self.meal_type_combo.set("Any")

        self.prep_time_entry = ttk.Entry(filter_box)
        self.prep_time_entry.grid(row=1, column=1, sticky="ew", padx=(0, 8), pady=(6, 0))
        self.prep_time_entry.insert(0, "30")

        self.match_preference_combo = ttk.Combobox(
            filter_box,
            state="readonly",
            style="Filter.TCombobox",
            values=["Partial", "Full", "All"],
        )
        self.match_preference_combo.grid(row=1, column=2, sticky="ew", pady=(6, 0))
        self.match_preference_combo.set("All")

        self.generate_meals_button = ttk.Button(
            parent,
            text="Generate Meal Recipes",
            style="Primary.TButton",
            command=self._on_generate_meals,
        )
        self.generate_meals_button.grid(row=3, column=0, sticky="ew", pady=(0, 12))

    def _build_results_list(self, parent: ttk.Frame) -> None:
        shell = ttk.Frame(parent, style="Panel.TFrame")
        shell.grid(row=0, column=0, sticky="nsew")
        shell.columnconfigure(0, weight=1)
        shell.rowconfigure(1, weight=1)

        ttk.Label(shell, text="Meal Feed", style="Section.TLabel").grid(row=0, column=0, sticky="w")

        list_frame = ttk.Frame(shell, style="SoftPanel.TFrame", padding=12)
        list_frame.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        self.results_list = tk.Listbox(
            list_frame,
            bg="#fffdf8",
            fg=self.TEXT,
            highlightthickness=0,
            relief="flat",
            selectbackground="#d8ebe3",
            selectforeground=self.TEXT,
            activestyle="none",
            font=("Helvetica", 11),
        )
        self.results_list.grid(row=0, column=0, sticky="nsew")
        self.results_list.bind("<<ListboxSelect>>", self._on_select_generated_meal)

        results_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.results_list.yview)
        results_scrollbar.grid(row=0, column=1, sticky="ns")
        self.results_list.configure(yscrollcommand=results_scrollbar.set)

    def _build_recipe_preview(self, parent: ttk.Frame) -> None:
        preview = ttk.Frame(parent, style="SoftPanel.TFrame", padding=14)
        preview.grid(row=0, column=0, sticky="nsew")
        preview.columnconfigure(0, weight=1)
        preview.rowconfigure(2, weight=1)

        ttk.Label(preview, text="Recipe Detail", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(preview, textvariable=self.selection_hint_var, style="Muted.TLabel").grid(row=1, column=0, sticky="w", pady=(4, 10))

        self.preview_text = tk.Text(
            preview,
            wrap="word",
            height=16,
            bg="#fffdf8",
            fg=self.TEXT,
            relief="flat",
            highlightthickness=0,
            padx=14,
            pady=14,
            font=("Helvetica", 11),
        )
        self.preview_text.grid(row=2, column=0, sticky="nsew")
        self.preview_text.configure(state="disabled")
        self._set_preview_text("Generate meals to populate this recipe detail view.")

    def _on_add_item(self) -> None:
        parsed = self._parse_form_fields()
        if parsed is None:
            return

        name, quantity, unit, category = parsed
        self.database.add_ingredient(
            pantry=self.pantry,
            name=name,
            quantity=quantity,
            unit=unit,
            category=category,
        )
        self._refresh_pantry_table()
        self._refresh_summary_cards()
        self.ingredient_entry.delete(0, tk.END)
        self.quantity_entry.delete(0, tk.END)
        self.ingredient_entry.focus_set()

    def _on_select_pantry_item(self, event: tk.Event) -> None:
        selected_ids = self.pantry_table.selection()
        if not selected_ids:
            self._selected_pantry_item_name = None
            return

        selected_item = self.pantry_table.item(selected_ids[0])
        values = selected_item.get("values", [])
        self._selected_pantry_item_name = str(values[0]) if values else None

    def _on_edit_selected(self) -> None:
        selected_ids = self.pantry_table.selection()
        if not selected_ids:
            messagebox.showinfo("No Selection", "Select a pantry item to edit.")
            return

        selected_item = self.pantry_table.item(selected_ids[0])
        ingredient_name, quantity, unit, category = selected_item["values"]
        self._open_edit_dialog(
            ingredient_name=str(ingredient_name),
            quantity=float(quantity),
            unit_value=str(unit),
            category_value=str(category),
        )

    def _open_edit_dialog(self, ingredient_name: str, quantity: float, unit_value: str, category_value: str) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Edit {ingredient_name}")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg=self.BACKGROUND)
        dialog.resizable(False, False)

        shell = ttk.Frame(dialog, style="Panel.TFrame", padding=18)
        shell.pack(fill="both", expand=True)
        shell.columnconfigure(1, weight=1)

        ttk.Label(shell, text="Ingredient", style="PanelText.TLabel").grid(row=0, column=0, sticky="w")
        name_entry = ttk.Entry(shell)
        name_entry.grid(row=0, column=1, sticky="ew", pady=(0, 10))
        name_entry.insert(0, ingredient_name)

        ttk.Label(shell, text="Quantity", style="PanelText.TLabel").grid(row=1, column=0, sticky="w")
        quantity_entry = ttk.Entry(shell)
        quantity_entry.grid(row=1, column=1, sticky="ew", pady=(0, 10))
        quantity_entry.insert(0, f"{quantity:g}")

        ttk.Label(shell, text="Unit", style="PanelText.TLabel").grid(row=2, column=0, sticky="w")
        unit_combo = ttk.Combobox(shell, state="readonly", style="Filter.TCombobox", values=[unit.value for unit in Unit])
        unit_combo.grid(row=2, column=1, sticky="ew", pady=(0, 10))
        unit_combo.set(unit_value)

        ttk.Label(shell, text="Category", style="PanelText.TLabel").grid(row=3, column=0, sticky="w")
        category_combo = ttk.Combobox(
            shell,
            state="readonly",
            style="Filter.TCombobox",
            values=[category.value for category in IngredientCategory],
        )
        category_combo.grid(row=3, column=1, sticky="ew", pady=(0, 16))
        category_combo.set(category_value)

        actions = ttk.Frame(shell, style="Panel.TFrame")
        actions.grid(row=4, column=0, columnspan=2, sticky="e")

        def save_changes() -> None:
            new_name = name_entry.get().strip()
            if not new_name:
                messagebox.showerror("Missing Ingredient", "Ingredient name cannot be empty.", parent=dialog)
                return

            try:
                new_quantity = float(quantity_entry.get().strip())
                if new_quantity <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Invalid Quantity", "Quantity must be a positive number.", parent=dialog)
                return

            self.pantry.remove_item(ingredient_name)
            self.database.add_ingredient(
                pantry=self.pantry,
                name=new_name,
                quantity=new_quantity,
                unit=Unit(unit_combo.get()),
                category=IngredientCategory(category_combo.get()),
            )
            self._refresh_pantry_table()
            self._refresh_summary_cards()
            dialog.destroy()

        ttk.Button(actions, text="Cancel", style="Secondary.TButton", command=dialog.destroy).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Save Changes", style="Primary.TButton", command=save_changes).pack(side="left")

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
        self._refresh_summary_cards()

    def _on_clear_pantry(self) -> None:
        if not self.pantry.list_items():
            return

        confirmed = messagebox.askyesno("Clear Pantry", "Remove all pantry items?")
        if not confirmed:
            return

        self.pantry = Pantry()
        self.database.save_pantry(self.pantry)
        self._refresh_pantry_table()
        self._refresh_summary_cards()

    def _on_save_pantry(self) -> None:
        self.database.save_pantry(self.pantry)
        messagebox.showinfo("Pantry Saved", "Pantry saved to pantry.json.")

    def _on_load_pantry(self) -> None:
        self.pantry = self.database.load_pantry()
        self._refresh_pantry_table()
        self._refresh_summary_cards()
        messagebox.showinfo("Pantry Loaded", "Pantry loaded from pantry.json.")

    def _on_generate_meals(self) -> None:
        max_prep_time = self._parse_max_prep_time()
        if max_prep_time is None and self.prep_time_entry.get().strip():
            return

        meal_type = self.meal_type_combo.get()
        match_preference = self.match_preference_combo.get()
        self._generation_request_id += 1
        request_id = self._generation_request_id

        self.generated_meals = self.meal_generator.generate_top_meals(
            self.pantry,
            limit=self.MAX_RECIPE_OUTPUTS,
            meal_type=meal_type,
            max_prep_time_minutes=max_prep_time,
            match_preference=match_preference,
        )

        self._ai_recipe_loading = True
        self.selection_hint_var.set("Building a specialized AI recipe and refreshing the meal feed.")
        self._refresh_generated_meals_list()
        self._refresh_summary_cards()

        if not self.generated_meals:
            self._set_preview_text("Loading specialized recipe suggestion...")
        else:
            self.results_list.selection_clear(0, tk.END)
            self.results_list.selection_set(0)
            self._set_preview_text("Loading specialized recipe suggestion...")

        self._start_ai_recipe_generation(
            request_id,
            meal_type=meal_type,
            max_prep_time_minutes=max_prep_time,
            match_preference=match_preference,
        )

    def _start_ai_recipe_generation(
        self,
        request_id: int,
        meal_type: str,
        max_prep_time_minutes: int | None,
        match_preference: str,
    ) -> None:
        worker = Thread(
            target=self._generate_ai_recipe_worker,
            args=(request_id, meal_type, max_prep_time_minutes, match_preference),
            daemon=True,
        )
        worker.start()

    def _generate_ai_recipe_worker(
        self,
        request_id: int,
        meal_type: str,
        max_prep_time_minutes: int | None,
        match_preference: str,
    ) -> None:
        recommendation = self.ai_recipe_generator.generate_recipe(
            self.pantry,
            meal_type=meal_type,
            max_prep_time_minutes=max_prep_time_minutes,
            match_preference=match_preference,
        )
        self.root.after(0, lambda: self._apply_ai_recipe_result(request_id, recommendation, match_preference))

    def _apply_ai_recipe_result(
        self,
        request_id: int,
        recommendation: MealRecommendation | None,
        match_preference: str,
    ) -> None:
        if request_id != self._generation_request_id:
            return

        self._ai_recipe_loading = False

        if recommendation is not None and self.meal_generator.matches_preference(recommendation, match_preference):
            self.generated_meals = [meal for meal in self.generated_meals if not meal.is_ai_generated]
            self.generated_meals.insert(0, recommendation)

        self.generated_meals = self.generated_meals[: self.MAX_RECIPE_OUTPUTS]

        self._refresh_generated_meals_list()
        self._refresh_summary_cards()

        if self.generated_meals:
            self.results_list.selection_clear(0, tk.END)
            self.results_list.selection_set(0)
            self._show_meal_preview(self.generated_meals[0])
        else:
            self.selection_hint_var.set("No meals matched yet. Add more pantry variety or loosen the filters.")
            self._set_preview_text("No recipe suggestions available for the current pantry and filters.")

    def _on_select_generated_meal(self, event: tk.Event) -> None:
        selection = self.results_list.curselection()
        if not selection:
            return

        selected_index = selection[0]
        if self._ai_recipe_loading:
            if selected_index == 0:
                self._set_preview_text("Loading specialized recipe suggestion...")
                return
            selected_index -= 1

        if selected_index >= len(self.generated_meals):
            return

        self._show_meal_preview(self.generated_meals[selected_index])

    def _show_meal_preview(self, recommendation: MealRecommendation) -> None:
        recipe = recommendation.recipe
        source_text = "AI specialized suggestion" if recommendation.is_ai_generated else "Template recommendation"
        ingredients = [
            f"- {ingredient.ingredient_name} ({ingredient.quantity:g} {ingredient.unit.value})"
            for ingredient in recipe.ingredients
        ]
        missing_text = ", ".join(category.value for category in recommendation.missing_categories) or "None"
        steps_text = "\n".join(f"{index}. {step}" for index, step in enumerate(recipe.steps, start=1))

        preview = (
            f"{recipe.name}\n\n"
            f"Source: {source_text}\n"
            f"Meal type: {recipe.meal_type.value}\n"
            f"Difficulty: {recipe.difficulty.value.title()}\n"
            f"Estimated time: {recipe.estimated_time_minutes} minutes\n"
            f"Pantry match: {recommendation.matched_slots}/{recommendation.total_slots} "
            f"({recommendation.match_rate:.0%})\n"
            f"Missing categories: {missing_text}\n\n"
            f"Ingredients:\n{chr(10).join(ingredients) if ingredients else '- No pantry ingredients selected'}\n\n"
            f"Steps:\n{steps_text}"
        )
        self.selection_hint_var.set(f"Viewing {recipe.name}")
        self._set_preview_text(preview)

    def _set_preview_text(self, content: str) -> None:
        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert("1.0", content)
        self.preview_text.configure(state="disabled")

    def _refresh_pantry_table(self) -> None:
        for item_id in self.pantry_table.get_children():
            self.pantry_table.delete(item_id)

        pantry_items = sorted(self.pantry.list_items(), key=lambda item: item.ingredient.name.lower())
        for pantry_item in pantry_items:
            self.pantry_table.insert(
                "",
                "end",
                values=(
                    pantry_item.ingredient.name,
                    f"{pantry_item.quantity:g}",
                    pantry_item.unit.value,
                    pantry_item.ingredient.category.value,
                ),
            )

    def _refresh_generated_meals_list(self) -> None:
        self.results_list.delete(0, tk.END)

        if self._ai_recipe_loading:
            self.results_list.insert(tk.END, "Loading specialized recipe...")
            self.results_list.itemconfig(0, bg="#edf5f1", fg=self.ACCENT)

        for recommendation in self.generated_meals:
            badge = "AI" if recommendation.is_ai_generated else "Template"
            label = (
                f"{badge}  |  {recommendation.recipe.name}  |  "
                f"{recommendation.recipe.estimated_time_minutes} min  |  "
                f"{recommendation.match_rate:.0%} match"
            )
            self.results_list.insert(tk.END, label)
            row_index = self.results_list.size() - 1
            if recommendation.is_ai_generated:
                self.results_list.itemconfig(row_index, bg="#fff3dd", fg=self.WARNING)

        if self.results_list.size() == 0:
            self.results_list.insert(tk.END, "No meal suggestions yet. Generate meals to populate the feed.")
            self.results_list.itemconfig(0, fg=self.MUTED)

    def _refresh_summary_cards(self) -> None:
        items = self.pantry.list_items()
        category_count = len({item.ingredient.category.value for item in items})
        meal_count = len(self.generated_meals)

        self.summary_items_var.set(str(len(items)))
        self.summary_categories_var.set(str(category_count))

        if self._ai_recipe_loading:
            self.summary_meals_var.set("Refreshing...")
        elif meal_count == 0:
            self.summary_meals_var.set("No suggestions")
        elif meal_count == 1:
            self.summary_meals_var.set("1 suggestion")
        else:
            self.summary_meals_var.set(f"{meal_count} suggestions")

    def _refresh_ai_status(self) -> None:
        status_text = self.ai_recipe_generator.get_status()
        self.ai_status_var.set(status_text)

        if status_text.startswith("AI ready:"):
            self.ai_status_label.configure(style="StatusReady.TLabel")
        elif status_text.startswith("AI unavailable:"):
            self.ai_status_label.configure(style="StatusOff.TLabel")
        else:
            self.ai_status_label.configure(style="StatusBusy.TLabel")

    def _parse_form_fields(self) -> tuple[str, float, Unit, IngredientCategory] | None:
        name = self.ingredient_entry.get().strip()
        if not name:
            messagebox.showerror("Missing Ingredient", "Please enter an ingredient name.")
            return None

        try:
            quantity = float(self.quantity_entry.get().strip())
            if quantity <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Quantity", "Quantity must be a positive number.")
            return None

        return (
            name,
            quantity,
            Unit(self.unit_combo.get()),
            IngredientCategory(self.category_combo.get()),
        )

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
    app = What2EatCleanGUI(root)
    root.mainloop()
