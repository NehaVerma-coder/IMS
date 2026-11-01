
import os
from decimal import Decimal, InvalidOperation

import mysql.connector
from flask import Flask, jsonify, render_template, request

app = Flask(
    __name__,
    template_folder=os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "templates"
    )
)


DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "152008")
DB_NAME = os.getenv("DB_NAME", "inventory_db")


def get_db():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )


def run(sql, params=(), fetch=False):
    conn = get_db()
    cur = conn.cursor(dictionary=True)

    try:
        cur.execute(sql, params)

        rows = cur.fetchall() if fetch else None

        if not fetch:
            conn.commit()

        return rows

    finally:
        cur.close()
        conn.close()


def validate_product(data):
    if not isinstance(data, dict):
        return None, "Invalid JSON data."

    name = str(data.get("name", "")).strip()
    category = str(data.get("category", "")).strip()

    if not name or not category:
        return None, "Name and category are required."

    try:
        quantity = int(data["quantity"])
        price = Decimal(str(data["price"]))

        if quantity < 0 or price < 0:
            return None, "Quantity and price cannot be negative."

        if not price.is_finite() or price > Decimal("99999999.99"):
            return None, "Enter a valid price."

    except (KeyError, ValueError, TypeError, InvalidOperation):
        return None, "Enter valid quantity and price."

    return {
        "name": name,
        "category": category,
        "quantity": quantity,
        "price": price
    }, None


# Open HTML page
@app.route("/")
def index():
    return render_template("index.html")


# Get all products
@app.route("/api/products", methods=["GET"])
def get_products():
    rows = run(
        """
        SELECT id, name, category, quantity, price
        FROM products
        ORDER BY id
        """,
        fetch=True
    )

    for row in rows:
        row["price"] = float(row["price"])

    return jsonify(rows)


# Add a product
@app.route("/api/products", methods=["POST"])
def add_product():
    data, error = validate_product(request.get_json(silent=True))

    if error:
        return jsonify(error=error), 400

    run(
        """
        INSERT INTO products (name, category, quantity, price)
        VALUES (%s, %s, %s, %s)
        """,
        (
            data["name"],
            data["category"],
            data["quantity"],
            data["price"]
        )
    )

    return jsonify(ok=True, message="Product added successfully."), 201


# Edit a product
@app.route("/api/products/<int:pid>", methods=["PUT"])
def edit_product(pid):
    data, error = validate_product(request.get_json(silent=True))

    if error:
        return jsonify(error=error), 400

    run(
        """
        UPDATE products
        SET name=%s, category=%s, quantity=%s, price=%s
        WHERE id=%s
        """,
        (
            data["name"],
            data["category"],
            data["quantity"],
            data["price"],
            pid
        )
    )

    return jsonify(ok=True, message="Product updated successfully.")


# Delete a product
@app.route("/api/products/<int:pid>", methods=["DELETE"])
def delete_product(pid):
    run(
        "DELETE FROM products WHERE id=%s",
        (pid,)
    )

    return jsonify(ok=True, message="Product deleted successfully.")


# Get or update settings
@app.route("/api/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}

        try:
            threshold = int(data["threshold"])

            if threshold < 0:
                raise ValueError

        except (KeyError, ValueError, TypeError):
            return jsonify(error="Enter a valid non-negative threshold."), 400

        run(
            """
            INSERT INTO settings (setting_key, setting_value)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE setting_value=VALUES(setting_value)
            """,
            ("threshold", str(threshold))
        )

    rows = run(
        """
        SELECT setting_value
        FROM settings
        WHERE setting_key=%s
        """,
        ("threshold",),
        fetch=True
    )

    threshold = int(rows[0]["setting_value"]) if rows else 10

    return jsonify(threshold=threshold)


if __name__ == "__main__":
    app.run(debug=True)
