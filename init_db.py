import sqlite3

DATABASE = "dineflow.db"


def initialize_database():
    connection = sqlite3.connect(DATABASE)
    connection.execute("PRAGMA foreign_keys = ON")

    cursor = connection.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS customers (
        customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        phone TEXT,
        email TEXT
    );

    CREATE TABLE IF NOT EXISTS restaurant_tables (
        table_id INTEGER PRIMARY KEY AUTOINCREMENT,
        table_number INTEGER NOT NULL UNIQUE,
        capacity INTEGER NOT NULL CHECK (capacity > 0),
        status TEXT NOT NULL DEFAULT 'available'
            CHECK (status IN ('available', 'occupied', 'reserved'))
    );

    CREATE TABLE IF NOT EXISTS menu_items (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL CHECK (price >= 0),
        available INTEGER NOT NULL DEFAULT 1
            CHECK (available IN (0, 1))
    );

    CREATE TABLE IF NOT EXISTS reservations (
        reservation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        table_id INTEGER,
        reservation_time TEXT NOT NULL,
        party_size INTEGER NOT NULL CHECK (party_size > 0),
        status TEXT NOT NULL DEFAULT 'booked'
            CHECK (status IN ('booked', 'seated', 'cancelled', 'completed')),
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
        FOREIGN KEY (table_id) REFERENCES restaurant_tables(table_id)
    );

    CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        table_id INTEGER,
        order_time TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        status TEXT NOT NULL DEFAULT 'pending'
            CHECK (status IN ('pending', 'preparing', 'ready', 'completed', 'cancelled')),
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
        FOREIGN KEY (table_id) REFERENCES restaurant_tables(table_id)
    );

    CREATE TABLE IF NOT EXISTS order_items (
        order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        item_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL CHECK (quantity > 0),
        unit_price REAL NOT NULL CHECK (unit_price >= 0),
        FOREIGN KEY (order_id) REFERENCES orders(order_id),
        FOREIGN KEY (item_id) REFERENCES menu_items(item_id),
        UNIQUE (order_id, item_id)
    );

    CREATE TABLE IF NOT EXISTS payments (
        payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        amount REAL NOT NULL CHECK (amount >= 0),
        payment_method TEXT NOT NULL
            CHECK (payment_method IN ('cash', 'card', 'other')),
        payment_time TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (order_id) REFERENCES orders(order_id)
    );
    """)

    # Add sample data so we can test the database.
    cursor.executemany("""
        INSERT OR IGNORE INTO restaurant_tables
            (table_id, table_number, capacity, status)
        VALUES (?, ?, ?, ?)
    """, [
        (1, 1, 2, "available"),
        (2, 2, 4, "available"),
        (3, 3, 6, "available"),
    ])

    cursor.executemany("""
        INSERT OR IGNORE INTO customers
            (customer_id, first_name, last_name, phone, email)
        VALUES (?, ?, ?, ?, ?)
    """, [
        (1, "Jordan", "Smith", "555-0101", "jordan@example.com"),
        (2, "Taylor", "Brown", "555-0102", "taylor@example.com"),
    ])

    cursor.executemany("""
        INSERT OR IGNORE INTO menu_items
            (item_id, name, description, price)
        VALUES (?, ?, ?, ?)
    """, [
        (1, "Classic Burger", "Beef burger with lettuce and tomato", 12.99),
        (2, "Caesar Salad", "Romaine, parmesan, and Caesar dressing", 8.99),
        (3, "French Fries", "Crispy seasoned fries", 3.99),
    ])

    connection.commit()

    # Verify that the tables were created.
    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name
    """)

    print("Database initialized successfully!")
    print("Tables created:")

    for row in cursor.fetchall():
        print(f" - {row[0]}")

    connection.close()


if __name__ == "__main__":
    initialize_database()
