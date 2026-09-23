import csv
import os
import random
from collections import Counter

INPUT_FILE = "/mnt/c/Users/Iman/Downloads/restouran/restaurant-menus.csv"
OUTPUT_FILE = "filtered_menu.csv"

# Сколько ресторанов хотим оставить
TARGET_RESTAURANTS = 1000

# Максимальное количество блюд одного ресторана.
# Это защищает выборку от ресторанов с тысячами/десятками тысяч позиций.
MAX_ITEMS_PER_RESTAURANT = 300

# Для воспроизводимости
RANDOM_SEED = 42


def clean_text(value):
    """Очистка обычного текстового поля."""
    if value is None:
        return ""

    return " ".join(value.strip().split())


def clean_price(value):
    """
    Преобразует:
        '15.99 USD' -> '15.99'
        '6.8 USD'   -> '6.8'

    Возвращает float или None.
    """
    if not value:
        return None

    value = value.strip()

    # Берём первое числовое значение.
    number = ""

    decimal_found = False

    for char in value:
        if char.isdigit():
            number += char
        elif char == "." and not decimal_found:
            number += char
            decimal_found = True
        elif number:
            break

    if not number:
        return None

    try:
        return float(number)
    except ValueError:
        return None


def scan_restaurants():
    """
    Первый проход по CSV.

    Определяем:
    - сколько menu items есть у каждого ресторана;
    - какие restaurant_id присутствуют в меню.
    """

    counts = Counter()

    print("Pass 1/2: scanning restaurant menu counts...")

    with open(INPUT_FILE, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            restaurant_id = row.get("restaurant_id", "").strip()

            if restaurant_id:
                counts[restaurant_id] += 1

    print(f"Restaurants with menu: {len(counts):,}")
    print(f"Total menu rows: {sum(counts.values()):,}")

    return counts


def choose_restaurants(counts):
    """
    Выбираем рестораны с меню.

    Сначала удаляем рестораны, у которых слишком мало/слишком
    много данных, затем случайно выбираем TARGET_RESTAURANTS.
    """

    # Оставляем рестораны, у которых есть хотя бы 1 блюдо.
    candidates = [
        restaurant_id
        for restaurant_id, count in counts.items()
        if count > 0
    ]

    if len(candidates) <= TARGET_RESTAURANTS:
        selected = set(candidates)
    else:
        random.seed(RANDOM_SEED)
        selected = set(
            random.sample(candidates, TARGET_RESTAURANTS)
        )

    print(f"Selected restaurants: {len(selected):,}")

    return selected


def transform():
    """
    Второй проход:
    читает CSV и создаёт очищенный filtered_menu.csv.
    """

    counts = Counter()

    rows_written = 0
    rows_skipped = 0

    print("Pass 2/2: filtering and transforming...")

    with open(INPUT_FILE, "r", encoding="utf-8-sig", newline="") as infile, \
         open(OUTPUT_FILE, "w", encoding="utf-8", newline="") as outfile:

        reader = csv.DictReader(infile)

        fieldnames = [
            "restaurant_id",
            "category",
            "name",
            "description",
            "price",
        ]

        writer = csv.DictWriter(
            outfile,
            fieldnames=fieldnames
        )

        writer.writeheader()

        for row in reader:
            restaurant_id = row.get("restaurant_id", "").strip()

            if restaurant_id not in selected_restaurants:
                continue

            # Ограничиваем количество позиций одного ресторана.
            if counts[restaurant_id] >= MAX_ITEMS_PER_RESTAURANT:
                continue

            category = clean_text(row.get("category"))
            name = clean_text(row.get("name"))
            description = clean_text(row.get("description"))
            price = clean_price(row.get("price"))

            # Минимальная валидация
            if not name:
                rows_skipped += 1
                continue

            if price is None:
                rows_skipped += 1
                continue

            writer.writerow({
                "restaurant_id": restaurant_id,
                "category": category,
                "name": name,
                "description": description,
                "price": f"{price:.2f}",
            })

            counts[restaurant_id] += 1
            rows_written += 1

    print()
    print("=" * 50)
    print("ETL FINISHED")
    print("=" * 50)
    print(f"Selected restaurants : {len(selected_restaurants):,}")
    print(f"Rows written         : {rows_written:,}")
    print(f"Rows skipped         : {rows_skipped:,}")
    print(f"Output file          : {OUTPUT_FILE}")
    print(f"Output size          : {os.path.getsize(OUTPUT_FILE) / 1024 / 1024:.2f} MB")
    print()

    print("Top restaurants by exported menu items:")

    for restaurant_id, count in counts.most_common(10):
        print(f"  {restaurant_id}: {count}")


if __name__ == "__main__":

    # Первый проход
    restaurant_counts = scan_restaurants()

    # Выбор ресторанов
    selected_restaurants = choose_restaurants(
        restaurant_counts
    )

    # Второй проход
    transform()
