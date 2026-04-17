from database import add_product, get_all_products

products = [
    "Молоко", "Хлеб", "Яйца", "Сыр", "Масло сливочное",
    "Колбаса", "Печенье", "Йогурт", "Творог", "Сметана",
    "Рис", "Гречка", "Макароны", "Сахар", "Соль",
    "Чай", "Кофе", "Сок", "Вода", "Помидоры", "Огурцы"
]

existing = [p.name for p in get_all_products()]

for name in products:
    if name not in existing:
        add_product(name)
        print(f"Добавлен товар: {name}")
    else:
        print(f"Уже есть: {name}")

print(f"\nВсего товаров в базе: {len(get_all_products())}")