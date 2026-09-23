import os
from fastapi import FastAPI, HTTPException
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI(title="Food Delivery & Analytics API", version="1.0.0")

# Переменные подключения берутся из окружения Docker Compose
DB_HOST = os.getenv("POSTGRES_HOST", "postgres")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "postgres")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "root")

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            cursor_factory=RealDictCursor
        )
        conn.autocommit = True
        conn.set_client_encoding('UTF8')
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

@app.get("/")
def root():
    return {"status": "ok", "message": "Food Delivery API is running"}

# 1. Список ресторанов
@app.get("/restaurants")
def get_restaurants(limit: int = 20, offset: int = 0):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT id, source_id, name, category, price_range, rating, rating_count, address, zip_code
            FROM public.restaurants
            ORDER BY id
            LIMIT %s OFFSET %s;
        """, (limit, offset))
        restaurants = cursor.fetchall()
        return {"limit": limit, "offset": offset, "data": restaurants}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

# 2. Детали конкретного ресторана и его блюд
@app.get("/restaurants/{restaurant_id}")
def get_restaurant_details(restaurant_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM public.restaurants WHERE id = %s;", (restaurant_id,))
        restaurant = cursor.fetchone()
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found")
            
        cursor.execute("SELECT * FROM public.dishes WHERE restaurant_id = %s;", (restaurant_id,))
        dishes = cursor.fetchall()
        
        return {
            "restaurant": restaurant,
            "menu": dishes
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

# 3. Список пользователей
@app.get("/users")
def get_users(limit: int = 50):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM public.users LIMIT %s;", (limit,))
        users = cursor.fetchall()
        return {"users": users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query error: {str(e)}")
    finally:
        cursor.close()
        conn.close()
