import tkinter as tk
from tkinter import ttk


class What2EatGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("What2Eat")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)

        self._configure_styles()
        self._build_layout()

    def _configure_styles(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Title.TLabel", font=("Arial", 22, "bold"))
        style.configure("Heading.TLabel", font=("Arial", 14, "bold"))
        style.configure("Card.TFrame", background="#f4f4f4", relief="flat")
        style.configure("Primary.TButton", font=("Arial", 11, "bold"), padding=10)
        style.configure("Secondary.TButton", font=("Arial", 10), padding=8)

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

        ttk.Button(input_row, text="Add Item", style="Primary.TButton").grid(
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
        ttk.Button(controls, text="Remove Selected", style="Secondary.TButton").pack(side="left", padx=8)
        ttk.Button(controls, text="Clear Pantry", style="Secondary.TButton").pack(side="left")

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

        ttk.Button(actions_frame, text="Generate Meals", style="Primary.TButton").grid(
            row=7, column=0, sticky="ew", pady=(18, 8)
        )
        ttk.Button(actions_frame, text="Save Pantry", style="Secondary.TButton").grid(
            row=8, column=0, sticky="ew", pady=(0, 8)
        )
        ttk.Button(actions_frame, text="Load Pantry", style="Secondary.TButton").grid(
            row=9, column=0, sticky="ew"
        )

    def _build_results_section(self, parent: ttk.Frame) -> None:
        results_frame = ttk.LabelFrame(parent, text="Generated Meals", padding=12)
        results_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)

        self.results_list = tk.Listbox(results_frame, height=10)
        self.results_list.grid(row=0, column=0, sticky="nsew")


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

if __name__ == "__main__":
    root = tk.Tk()
    app = What2EatGUI(root)
    root.mainloop()
