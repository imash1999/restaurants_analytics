import json
import random
import time
import os
import html
import uuid
from datetime import datetime

import psycopg2
import boto3
from kafka import KafkaProducer


# =========================
# Environment
# =========================

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "order-events")

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "postgres")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "root")


# =========================
# PostgreSQL
# =========================

def get_db_connection():
    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )


# =========================
# MinIO
# =========================

s3_client = boto3.client(
    "s3",
    endpoint_url="http://minio:9000",
    aws_access_key_id="minioadmin",
    aws_secret_access_key="minioadminpassword"
)

def send_to_minio(event_data):
    try:
        try:
            s3_client.create_bucket(Bucket="raw-events")
        except Exception:
            pass

        file_path = (
            f"orders/"
            f"{datetime.now().strftime('%Y-%m-%d')}/"
            f"order_{datetime.now().strftime('%H%M%S_%f')}.json"
        )

        s3_client.put_object(
            Bucket="raw-events",
            Key=file_path,
            Body=json.dumps(event_data)
        )
    except Exception as e:
        print(f"MinIO error: {e}")


# =========================
# Kafka
# =========================

print(f"Connecting to Kafka: {KAFKA_BOOTSTRAP_SERVERS}")

producer = None
while producer is None:
    try:
        producer = KafkaProducer(
            bootstrap_servers=[KAFKA_BOOTSTRAP_SERVERS],
            value_serializer=lambda v: json.dumps(v).encode("utf-8")
        )
        print("Kafka connected")
    except Exception as e:
        print(f"Kafka waiting: {e}")
        time.sleep(3)


# =========================
# Generate Order Event
# =========================

def generate_order_event():
    conn = get_db_connection()
    cur = conn.cursor()

    # 1. Случайный пользователь
    cur.execute("""
        SELECT id
        FROM public.users
        ORDER BY random()
        LIMIT 1;
    """)
    user_row = cur.fetchone()
    if not user_row:
        cur.close()
        conn.close()
        raise Exception("No users found in database")
    user_id = user_row[0]

    # 2. Случайный ресторан, у которого есть блюда
    cur.execute("""
        SELECT r.id
        FROM public.restaurants r
        JOIN public.dishes d ON r.id = d.restaurant_id
        WHERE d.price > 0
        GROUP BY r.id
        ORDER BY random()
        LIMIT 1;
    """)
    rest_row = cur.fetchone()
    if not rest_row:
        cur.close()
        conn.close()
        raise Exception("No restaurants with dishes found in database")
    restaurant_id = rest_row[0]

    # 3. Случайные блюда из выбранного ресторана
    cur.execute("""
        SELECT id, name, price
        FROM public.dishes
        WHERE restaurant_id = %s AND price > 0
        ORDER BY random()
        LIMIT %s;
    """, (restaurant_id, random.randint(1, 3)))

    dishes = cur.fetchall()

    if not dishes:
        cur.close()
        conn.close()
        return generate_order_event()

    items = []
    total_amount = 0.0

    for dish in dishes:
        quantity = random.randint(1, 3)
        price = float(dish[2])
        total = price * quantity
        total_amount += total

        item = {
            "dish_id": dish[0],
            "name": html.unescape(dish[1]) if dish[1] else "Dish",
            "quantity": quantity,
            "unit_price": price
        }
        items.append(item)

    cur.close()
    conn.close()

    event = {
        "event_id": str(uuid.uuid4()),
        "event_type": "order_created",
        "user_id": user_id,
        "restaurant_id": restaurant_id,
        "items": items,
        "total_amount": round(total_amount, 2),
        "status": "created",
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    }

    return event


# =========================
# Main
# =========================

if __name__ == "__main__":
    print(f"Starting order generator for topic: {KAFKA_TOPIC}")

    while True:
        try:
            order = generate_order_event()

            producer.send(KAFKA_TOPIC, value=order)
            send_to_minio(order)

            print(
                f"Order created | "
                f"user={order['user_id']} | "
                f"restaurant={order['restaurant_id']} | "
                f"amount={order['total_amount']}"
            )

            time.sleep(random.uniform(1, 3))

        except Exception as e:
            print(f"Generator error: {e}")
            time.sleep(5)
