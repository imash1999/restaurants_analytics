import os
import hashlib
import hmac
import secrets
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI(title="Food Delivery & Analytics API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3080"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        310000
    )

    return (
        "pbkdf2_sha256$310000$"
        + salt.hex()
        + "$"
        + password_hash.hex()
    )

def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations, salt_hex, hash_hex = stored_hash.split("$")

        if algorithm != "pbkdf2_sha256":
            return False

        salt = bytes.fromhex(salt_hex)

        calculated_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            int(iterations)
        )

        return hmac.compare_digest(
            calculated_hash.hex(),
            hash_hex
        )

    except (ValueError, TypeError):
        return False

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


@app.post("/auth/register")
def register_user(
    username: str,
    email: str,
    password: str,
    name: str = ""
):
    username = username.strip()
    email = email.strip().lower()
    name = name.strip()

    if not username:
        raise HTTPException(
            status_code=400,
            detail="Username is required"
        )

    if not email:
        raise HTTPException(
            status_code=400,
            detail="Email is required"
        )

    if len(password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 6 characters"
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id
            FROM public.users
            WHERE username = %s;
            """,
            (username,)
        )

        if cursor.fetchone():
            raise HTTPException(
                status_code=409,
                detail="Username already exists"
            )

        cursor.execute(
            """
            SELECT id
            FROM public.users
            WHERE LOWER(email) = LOWER(%s);
            """,
            (email,)
        )

        if cursor.fetchone():
            raise HTTPException(
                status_code=409,
                detail="Email already exists"
            )

        password_hash = hash_password(password)

        cursor.execute(
            """
            INSERT INTO public.users
                (username, email, password_hash, name)
            VALUES
                (%s, %s, %s, %s)
            RETURNING id, username, email, name, created_at;
            """,
            (
                username,
                email,
                password_hash,
                name
            )
        )

        user = cursor.fetchone()

        return {
            "message": "Registration successful",
            "user": user
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Registration error: {str(e)}"
        )

    finally:
        cursor.close()
        conn.close()

@app.post("/auth/login")
def login_user(
    username: str,
    password: str
):
    username = username.strip()

    if not username or not password:
        raise HTTPException(
            status_code=400,
            detail="Username and password are required"
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, username, email, password_hash, name, created_at
            FROM public.users
            WHERE username = %s;
            """,
            (username,)
        )

        user = cursor.fetchone()

        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid username or password"
            )

        if not user["password_hash"]:
            raise HTTPException(
                status_code=401,
                detail="This account does not have a usable password"
            )

        if not verify_password(
            password,
            user["password_hash"]
        ):
            raise HTTPException(
                status_code=401,
                detail="Invalid username or password"
            )

        return {
            "message": "Login successful",
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "name": user["name"],
                "created_at": user["created_at"]
            }
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Login error: {str(e)}"
        )

    finally:
        cursor.close()
        conn.close()