
import os
import mysql.connector
from werkzeug.security import generate_password_hash

# Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "152008")
DB_NAME = "inventory_db"


def main():
    # Connect to MySQL server
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD
    )

    cur = conn.cursor()

    try:
        # Create and select database
        cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        cur.execute(f"USE {DB_NAME}")

        # Users table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                role ENUM('admin', 'staff') DEFAULT 'staff',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Suppliers table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS suppliers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                phone VARCHAR(20),
                email VARCHAR(100),
                address VARCHAR(255)
            )
        """)

        # Products table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                category VARCHAR(100) NOT NULL,
                quantity INT NOT NULL DEFAULT 0,
                price DECIMAL(10,2) NOT NULL DEFAULT 0,
                supplier_id INT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CHECK (quantity >= 0),
                CHECK (price >= 0),
                FOREIGN KEY (supplier_id)
                    REFERENCES suppliers(id)
                    ON DELETE SET NULL
            )
        """)

        # Stock movement history
        cur.execute("""
            CREATE TABLE IF NOT EXISTS stock_movements (
                id INT AUTO_INCREMENT PRIMARY KEY,
                product_id INT NOT NULL,
                movement_type ENUM('IN', 'OUT') NOT NULL,
                quantity INT NOT NULL,
                note VARCHAR(255),
                moved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id)
                    REFERENCES products(id)
                    ON DELETE CASCADE
            )
        """)

        # Application settings
        cur.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                setting_key VARCHAR(50) PRIMARY KEY,
                setting_value VARCHAR(100) NOT NULL
            )
        """)

        conn.commit()
        print("Database and tables are ready.")

        # Create default admin only if missing
        cur.execute(
            "SELECT id FROM users WHERE username = %s",
            ("admin",)
        )

        if cur.fetchone() is None:
            cur.execute("""
                INSERT INTO users (username, password_hash, role)
                VALUES (%s, %s, 'admin')
            """, (
                "admin",
                generate_password_hash("admin123")
            ))

        # Add suppliers if missing
        suppliers = [
            ("TechWorld Distributors", "9876543210",
             "sales@techworld.example", "Indore"),
            ("Office Mart", "9123456780",
             "hello@officemart.example", "Bhopal")
        ]

        for supplier in suppliers:
            cur.execute("""
                SELECT id FROM suppliers WHERE name = %s
                LIMIT 1
            """, (supplier[0],))

            if cur.fetchone() is None:
                cur.execute("""
                    INSERT INTO suppliers (name, phone, email, address)
                    VALUES (%s, %s, %s, %s)
                """, supplier)

        conn.commit()

        # Sample products: name, category, quantity, price
        products = [
            ("Laptop", "Electronics", 25, 55000.00),
            ("Keyboard", "Accessories", 8, 800.00),
            ("Mouse", "Accessories", 40, 500.00),
            ("Monitor", "Electronics", 15, 12000.00),
            ("USB Cable", "Accessories", 30, 150.00),
            ("Printer", "Electronics", 5, 8500.00),
            ("Webcam", "Electronics", 12, 1800.00),
            ("Headphones", "Accessories", 20, 1200.00),
            ("Pen Drive", "Storage", 18, 650.00),
            ("Router", "Networking", 7, 2200.00),
            ("ESP32 Development Board", "Electronics", 50, 500.00),
            ("Temperature Sensor", "Sensors", 25, 180.00),
            ("Relay Module", "Electronics", 15, 120.00),
            ("Power Supply", "Electrical", 10, 950.00),
            ("Jumper Wires", "Accessories", 60, 80.00)
        ]

        added = 0

        for product in products:
            cur.execute("""
                SELECT id FROM products
                WHERE name = %s AND category = %s
                LIMIT 1
            """, (product[0], product[1]))

            if cur.fetchone() is None:
                cur.execute("""
                    INSERT INTO products
                        (name, category, quantity, price)
                    VALUES (%s, %s, %s, %s)
                """, product)

                added += 1

        # Default low-stock threshold
        cur.execute("""
            INSERT IGNORE INTO settings (setting_key, setting_value)
            VALUES ('threshold', '10')
        """)

        conn.commit()

        print(f"Added {added} new sample products.")
        print("\nCurrent inventory:")

        cur.execute("""
            SELECT id, name, category, quantity, price
            FROM products
            ORDER BY id
        """)

        for row in cur.fetchall():
            print(row)

        print("\nSetup completed successfully.")
        print("Default login: admin / admin123")

    except mysql.connector.Error as error:
        conn.rollback()
        print("MySQL error:", error)

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
