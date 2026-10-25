from functools import wraps
from flask import Flask, render_template, request, jsonify, session
import mysql.connector
from mysql.connector import Error
import os

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "change-this-secret-key")

# Update these values for your local MySQL setup, or set environment variables.
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", "YOUR_MYSQL_PASSWORD"),
    "database": os.environ.get("DB_NAME", "inventory_db"),
}

DEMO_PRODUCTS = [
    ("Laptop", "Electronics", 25, 55000.00),
    ("Keyboard", "Accessories", 8, 800.00),
    ("Mouse", "Accessories", 40, 500.00),
    ("Monitor", "Electronics", 15, 12000.00),
]

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return jsonify({"error": "Please log in first."}), 401
        return fn(*args, **kwargs)
    return wrapper

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(120) NOT NULL,
            category VARCHAR(100) NOT NULL,
            quantity INT NOT NULL DEFAULT 0,
            price DECIMAL(12,2) NOT NULL DEFAULT 0
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS app_settings (
            setting_key VARCHAR(50) PRIMARY KEY,
            setting_value VARCHAR(100) NOT NULL
        )
    """)
    cur.execute(
        "INSERT IGNORE INTO app_settings (setting_key, setting_value) VALUES ('low_stock_threshold', '10')"
    )
    cur.execute("SELECT COUNT(*) FROM products")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO products (name, category, quantity, price) VALUES (%s,%s,%s,%s)",
            DEMO_PRODUCTS
        )
    conn.commit()
    cur.close()
    conn.close()

def fetch_settings(cur):
    cur.execute("SELECT setting_value FROM app_settings WHERE setting_key='low_stock_threshold'")
    row = cur.fetchone()
    return {"threshold": int(row[0]) if row else 10}

def fetch_products(cur):
    cur.execute("SELECT id, name, category, quantity, price FROM products ORDER BY id")
    return [
        {"id": row[0], "name": row[1], "category": row[2],
         "quantity": int(row[3]), "price": float(row[4])}
        for row in cur.fetchall()
    ]

@app.route("/")
def index():
    return render_template("index.html")

@app.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}
    # Demo credentials for college demonstration only.
    if data.get("username") == "admin" and data.get("password") == "admin123":
        session["logged_in"] = True
        return jsonify({"message": "Login successful"})
    return jsonify({"error": "Incorrect username or password."}), 401

@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})