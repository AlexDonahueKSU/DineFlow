import sqlite3
from pathlib import Path

from flask import (
    Flask,
    render_template_string,
    request,
    redirect,
    url_for,
    flash,
)

app = Flask(__name__)
app.secret_key = "dineflow-local-dev-key"

# Always find the database next to this Python file.
DATABASE = Path(__file__).resolve().parent / "dineflow.db"


def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


@app.route("/")
def dashboard():
    with get_db() as db:
        menu_items = db.execute("""
            SELECT item_id, name, description, price, available
            FROM menu_items
            ORDER BY name
        """).fetchall()

        tables = db.execute("""
            SELECT table_id, table_number, capacity, status
            FROM restaurant_tables
            ORDER BY table_number
        """).fetchall()

        customers = db.execute("""
            SELECT customer_id, first_name, last_name, phone, email
            FROM customers
            ORDER BY last_name, first_name
        """).fetchall()

        reservations = db.execute("""
            SELECT
                r.reservation_id,
                r.reservation_time,
                r.party_size,
                r.status,
                c.first_name,
                c.last_name,
                t.table_number
            FROM reservations r
            JOIN customers c
                ON r.customer_id = c.customer_id
            LEFT JOIN restaurant_tables t
                ON r.table_id = t.table_id
            ORDER BY r.reservation_time
        """).fetchall()

        counts = {
            "menu": db.execute(
                "SELECT COUNT(*) FROM menu_items"
            ).fetchone()[0],
            "tables": db.execute(
                "SELECT COUNT(*) FROM restaurant_tables"
            ).fetchone()[0],
            "customers": db.execute(
                "SELECT COUNT(*) FROM customers"
            ).fetchone()[0],
            "orders": db.execute(
                "SELECT COUNT(*) FROM orders"
            ).fetchone()[0],
        }

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport"
              content="width=device-width, initial-scale=1">
        <title>DineFlow Dashboard</title>
        <style>
            * { box-sizing: border-box; }

            body {
                margin: 0;
                font-family: Arial, sans-serif;
                background: #f4f6f8;
                color: #253044;
            }

            header {
                background: #173c35;
                color: white;
                padding: 24px 6%;
            }

            header h1 { margin: 0 0 6px; }
            header p { margin: 0; color: #d5e8df; }

            nav {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 20px;
                    margin-top: 20px;
                }

                nav a {
                    color: white;
                    text-decoration: none;
                    padding: 8px 12px;
                    border: 1px solid #ffffff55;
                    border-radius: 6px;
                }

                nav a:hover {
                    background: #ffffff22;
                }

            main {
                max-width: 1100px;
                margin: 30px auto;
                padding: 0 20px;
            }

            .stats {
                display: grid;
                grid-template-columns: repeat(
                    auto-fit, minmax(170px, 1fr)
                );
                gap: 16px;
                margin-bottom: 28px;
            }

            .stat, section {
                background: white;
                padding: 22px;
                border-radius: 10px;
                box-shadow: 0 2px 8px #0000000a;
            }

            .stat p { margin: 0 0 8px; color: #64748b; }
            .stat strong { font-size: 30px; }

            section { margin-bottom: 24px; overflow-x: auto; }
            h2 { margin-top: 0; }

            table {
                width: 100%;
                border-collapse: collapse;
                text-align: left;
            }

            th, td {
                padding: 12px;
                border-bottom: 1px solid #e5e7eb;
            }

            th { color: #64748b; font-size: 13px; }

            .status {
                display: inline-block;
                padding: 5px 9px;
                border-radius: 20px;
                background: #e4f5e9;
                color: #216e39;
                font-size: 12px;
            }

            .unavailable {
                background: #fee2e2;
                color: #991b1b;
            }

            footer {
                text-align: center;
                padding: 20px;
                color: #64748b;
            }
        </style>
    </head>
    <body>
        <header>
            <h1>DineFlow</h1>
            <p>Restaurant Management System</p>
            <nav>
                <a href="/">Dashboard</a>
                <a href="/orders">Orders</a>
            </nav>
        </header>

        <main>
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% for category, message in messages %}
                <p style="padding: 12px; background: #e4f5e9;">
                    {{ message }}
                </p>
                {% endfor %}
            {% endwith %}
            <section>
                <h2>Make a Reservation</h2>

                <form action="/reservations" method="POST">
                    <label for="customer_id">Customer</label>
                    <select id="customer_id" name="customer_id" required>
                        {% for customer in customers %}
                        <option value="{{ customer.customer_id }}">
                            {{ customer.first_name }} {{ customer.last_name }}
                        </option>
                        {% endfor %}
                    </select>

                    <label for="table_id">Table</label>
                    <select id="table_id" name="table_id" required>
                        {% for table in tables %}
                        <option value="{{ table.table_id }}">
                            Table {{ table.table_number }}
                            ({{ table.capacity }} seats)
                        </option>
                        {% endfor %}
                    </select>

                    <label for="party_size">Party Size</label>
                    <input
                        type="number"
                        id="party_size"
                        name="party_size"
                        min="1"
                        value="2"
                        required
                    >

                    <label for="reservation_time">Date and Time</label>
                    <input
                        type="datetime-local"
                        id="reservation_time"
                        name="reservation_time"
                        required
                    >

                    <button type="submit">Create Reservation</button>
                </form>
            </section>
            <div class="stats">
                <div class="stat">
                    <p>Menu Items</p>
                    <strong>{{ counts.menu }}</strong>
                </div>
                <div class="stat">
                    <p>Restaurant Tables</p>
                    <strong>{{ counts.tables }}</strong>
                </div>
                <div class="stat">
                    <p>Customers</p>
                    <strong>{{ counts.customers }}</strong>
                </div>
                <div class="stat">
                    <p>Total Orders</p>
                    <strong>{{ counts.orders }}</strong>
                </div>
            </div>

            <section>
                <h2>Restaurant Tables</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Table</th>
                            <th>Capacity</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for table in tables %}
                        <tr>
                            <td>{{ table.table_number }}</td>
                            <td>{{ table.capacity }} guests</td>
                            <td>
                                <span class="status
                                    {% if table.status != 'available' %}
                                    unavailable{% endif %}">
                                    {{ table.status | title }}
                                </span>
                            </td>
                        </tr>
                        {% else %}
                        <tr><td colspan="3">No tables found.</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </section>

            <section>
                <h2>Menu</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Item</th>
                            <th>Description</th>
                            <th>Price</th>
                            <th>Availability</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for item in menu_items %}
                        <tr>
                            <td>{{ item.name }}</td>
                            <td>{{ item.description or '—' }}</td>
                            <td>${{ "%.2f" | format(item.price) }}</td>
                            <td>
                                {% if item.available %}
                                <span class="status">Available</span>
                                {% else %}
                                <span class="status unavailable">
                                    Unavailable
                                </span>
                                {% endif %}
                            </td>
                        </tr>
                        {% else %}
                        <tr><td colspan="4">No menu items found.</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </section>
            <section>
                <h2>Reservations</h2>

                <table>
                    <thead>
                        <tr>
                            <th>Customer</th>
                            <th>Date / Time</th>
                            <th>Party</th>
                            <th>Table</th>
                            <th>Status</th>
                        </tr>
                    </thead>

                    <tbody>
                        {% for reservation in reservations %}
                        <tr>
                            <td>
                                {{ reservation.first_name }}
                                {{ reservation.last_name }}
                            </td>
                            <td>{{ reservation.reservation_time }}</td>
                            <td>{{ reservation.party_size }}</td>
                            <td>{{ reservation.table_number }}</td>
                            <td>{{ reservation.status | title }}</td>
                        </tr>
                        {% else %}
                        <tr>
                            <td colspan="5">No reservations yet.</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </section>
            <section>
                <h2>Customers</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Phone</th>
                            <th>Email</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for customer in customers %}
                        <tr>
                            <td>{{ customer.first_name }}
                                {{ customer.last_name }}</td>
                            <td>{{ customer.phone or '—' }}</td>
                            <td>{{ customer.email or '—' }}</td>
                        </tr>
                        {% else %}
                        <tr><td colspan="3">No customers found.</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </section>
        </main>

        <footer>DineFlow · Local Restaurant Management</footer>
    </body>
    </html>
    """, menu_items=menu_items, tables=tables,
       customers=customers, counts=counts, reservations=reservations)

from datetime import datetime


@app.route("/reservations", methods=["POST"])
def create_reservation():
    # Read the submitted form.
    try:
        customer_id = int(request.form["customer_id"])
        table_id = int(request.form["table_id"])
        party_size = int(request.form["party_size"])
        reservation_time = request.form["reservation_time"]

        # Validate the date/time format from the browser.
        requested_time = datetime.strptime(
            reservation_time, "%Y-%m-%dT%H:%M"
        )

        if requested_time <= datetime.now():
            flash("Please choose a future reservation time.", "error")
            return redirect(url_for("dashboard"))

        if party_size <= 0:
            flash("Party size must be at least one.", "error")
            return redirect(url_for("dashboard"))

    except (KeyError, ValueError):
        flash("Please provide valid reservation details.", "error")
        return redirect(url_for("dashboard"))

    db = get_db()

    try:
        # Confirm that the customer exists.
        customer = db.execute(
            "SELECT customer_id FROM customers WHERE customer_id = ?",
            (customer_id,),
        ).fetchone()

        if customer is None:
            flash("Customer not found.", "error")
            return redirect(url_for("dashboard"))

        # Confirm that the table exists and can seat the party.
        table = db.execute("""
            SELECT table_id, capacity
            FROM restaurant_tables
            WHERE table_id = ?
        """, (table_id,)).fetchone()

        if table is None:
            flash("Table not found.", "error")
            return redirect(url_for("dashboard"))

        if party_size > table["capacity"]:
            flash(
                f"This table seats only {table['capacity']} guests.",
                "error",
            )
            return redirect(url_for("dashboard"))

        # Reservations last two hours.
        # Reject overlapping bookings for this table.
        conflict = db.execute("""
            SELECT reservation_id
            FROM reservations
            WHERE table_id = ?
              AND status IN ('booked', 'seated')
              AND datetime(reservation_time) <
                  datetime(?, '+2 hours')
              AND datetime(reservation_time, '+2 hours') >
                  datetime(?)
            LIMIT 1
        """, (table_id, reservation_time, reservation_time)).fetchone()

        if conflict:
            flash(
                "That table is already booked during this time. "
                "Please choose another table or time.",
                "error",
            )
            return redirect(url_for("dashboard"))

        # Save the reservation.
        db.execute("""
            INSERT INTO reservations (
                customer_id,
                table_id,
                reservation_time,
                party_size,
                status
            )
            VALUES (?, ?, ?, ?, 'booked')
        """, (
            customer_id,
            table_id,
            reservation_time,
            party_size,
        ))

        db.commit()
        flash("Reservation created successfully!", "success")
 
    except Exception:
        db.rollback()
        app.logger.exception("Failed to create reservation")
        flash("Something went wrong saving the reservation.", "error")

    finally:
        db.close()

    return redirect(url_for("dashboard"))

@app.route("/orders/<int:order_id>/status", methods=["POST"])
def update_order_status(order_id):
    new_status = request.form.get("status", "").strip().lower()

    # Only allow valid status changes.
    allowed_transitions = {
        "pending": {"preparing", "cancelled"},
        "preparing": {"ready", "cancelled"},
        "ready": {"completed", "cancelled"},
        "completed": set(),
        "cancelled": set(),
    }

    db = get_db()

    try:
        order = db.execute(
            "SELECT status FROM orders WHERE order_id = ?",
            (order_id,),
        ).fetchone()

        if order is None:
            flash(f"Order #{order_id} was not found.", "error")
            return redirect(url_for("manage_orders"))

        current_status = order["status"]

        if new_status not in allowed_transitions.get(current_status, set()):
            flash(
                f"Cannot change order #{order_id} "
                f"from {current_status} to {new_status}.",
                "error",
            )
            return redirect(url_for("manage_orders"))

        db.execute(
            "UPDATE orders SET status = ? WHERE order_id = ?",
            (new_status, order_id),
        )
        db.commit()

        flash(
            f"Order #{order_id} updated to {new_status.title()}.",
            "success",
        )

    except Exception:
        db.rollback()
        app.logger.exception("Failed to update order status")
        flash("Unable to update the order status.", "error")

    finally:
        db.close()

    return redirect(url_for("manage_orders"))

@app.route("/orders", methods=["GET", "POST"])
def manage_orders():
    if request.method == "POST":
        # Read the customer and table selections.
        try:
            customer_value = request.form.get("customer_id", "")
            table_value = request.form.get("table_id", "")

            customer_id = int(customer_value) if customer_value else None
            table_id = int(table_value) if table_value else None

            # Collect selected menu items and their quantities.
            selected_items = []

            db = get_db()

            try:
                if customer_id is not None:
                    customer = db.execute(
                        "SELECT customer_id FROM customers WHERE customer_id = ?",
                        (customer_id,),
                    ).fetchone()

                    if customer is None:
                        flash("Please select a valid customer.", "error")
                        return redirect(url_for("manage_orders"))

                if table_id is not None:
                    table = db.execute(
                        "SELECT table_id FROM restaurant_tables WHERE table_id = ?",
                        (table_id,),
                    ).fetchone()

                    if table is None:
                        flash("Please select a valid table.", "error")
                        return redirect(url_for("manage_orders"))

                menu_items = db.execute("""
                    SELECT item_id, name, price
                    FROM menu_items
                    WHERE available = 1
                """).fetchall()

                for item in menu_items:
                    raw_quantity = request.form.get(
                        f"quantity_{item['item_id']}", "0"
                    )

                    quantity = int(raw_quantity)

                    if quantity < 0:
                        flash("Quantities cannot be negative.", "error")
                        return redirect(url_for("manage_orders"))

                    if quantity > 0:
                        selected_items.append({
                            "item_id": item["item_id"],
                            "quantity": quantity,
                            "unit_price": item["price"],
                        })

                if not selected_items:
                    flash("Choose at least one menu item.", "error")
                    return redirect(url_for("manage_orders"))

                # Create the order and its line items together.
                cursor = db.execute("""
                    INSERT INTO orders (customer_id, table_id)
                    VALUES (?, ?)
                """, (customer_id, table_id))

                order_id = cursor.lastrowid

                for item in selected_items:
                    db.execute("""
                        INSERT INTO order_items
                            (order_id, item_id, quantity, unit_price)
                        VALUES (?, ?, ?, ?)
                    """, (
                        order_id,
                        item["item_id"],
                        item["quantity"],
                        item["unit_price"],
                    ))

                db.commit()
                flash(f"Order #{order_id} created successfully!", "success")

            except Exception:
                db.rollback()
                raise
            finally:
                db.close()

        except (ValueError, TypeError):
            flash("Please enter valid customer, table, and quantity values.", "error")

        except Exception:
            app.logger.exception("Failed to create order")
            flash("Unable to create the order. Please try again.", "error")

        return redirect(url_for("manage_orders"))

    # Load data for the order form and order history.
    with get_db() as db:
        customers = db.execute("""
            SELECT customer_id, first_name, last_name
            FROM customers
            ORDER BY last_name, first_name
        """).fetchall()

        tables = db.execute("""
            SELECT table_id, table_number, capacity
            FROM restaurant_tables
            ORDER BY table_number
        """).fetchall()

        menu_items = db.execute("""
            SELECT item_id, name, description, price
            FROM menu_items
            WHERE available = 1
            ORDER BY name
        """).fetchall()

        orders = db.execute("""
            SELECT
                o.order_id,
                o.order_time,
                o.status,
                c.first_name,
                c.last_name,
                t.table_number,
                COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS total,
                GROUP_CONCAT(
                    mi.name || ' x ' || oi.quantity, ', '
                ) AS item_summary
            FROM orders o
            LEFT JOIN customers c ON o.customer_id = c.customer_id
            LEFT JOIN restaurant_tables t ON o.table_id = t.table_id
            LEFT JOIN order_items oi ON o.order_id = oi.order_id
            LEFT JOIN menu_items mi ON oi.item_id = mi.item_id
            GROUP BY o.order_id
            ORDER BY o.order_id DESC
        """).fetchall()

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>DineFlow - Orders</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #f4f6f8;
                color: #253044;
                margin: 0;
            }
            header {
                background: #173c35;
                color: white;
                padding: 24px 6%;
            }
            main {
                max-width: 1100px;
                margin: 30px auto;
                padding: 0 20px;
            }
            section {
                background: white;
                padding: 22px;
                margin-bottom: 24px;
                border-radius: 10px;
                overflow-x: auto;
            }
            label { display: block; margin: 14px 0 6px; }
            select, input, button {
                padding: 10px;
                font: inherit;
            }
            select, input[type="number"] { max-width: 100%; }
            button {
                margin-top: 16px;
                background: #173c35;
                color: white;
                border: 0;
                border-radius: 5px;
                cursor: pointer;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                text-align: left;
            }
            th, td {
                padding: 12px;
                border-bottom: 1px solid #e5e7eb;
            }
            .message { padding: 12px; background: #e4f5e9; }
            .error { background: #fee2e2; }
            .menu-row {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 16px;
                padding: 10px 0;
                border-bottom: 1px solid #e5e7eb;
            }
            .menu-row input { width: 75px; }
            a { color: #216e58; }
        </style>
    </head>
    <body>
        <header>
            <h1>DineFlow - Order Management</h1>
            <a href="/" style="color:white">Back to Dashboard</a>
        </header>

        <main>
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% for category, message in messages %}
                    <p class="message {% if category == 'error' %}error{% endif %}">
                        {{ message }}
                    </p>
                {% endfor %}
            {% endwith %}

            <section>
                <h2>Create an Order</h2>

                <form method="POST" action="/orders">
                    <label for="customer_id">Customer (optional)</label>
                    <select id="customer_id" name="customer_id">
                        <option value="">Walk-in / Takeout</option>
                        {% for customer in customers %}
                            <option value="{{ customer.customer_id }}">
                                {{ customer.first_name }} {{ customer.last_name }}
                            </option>
                        {% endfor %}
                    </select>

                    <label for="table_id">Table (optional)</label>
                    <select id="table_id" name="table_id">
                        <option value="">No table / Takeout</option>
                        {% for table in tables %}
                            <option value="{{ table.table_id }}">
                                Table {{ table.table_number }}
                                ({{ table.capacity }} seats)
                            </option>
                        {% endfor %}
                    </select>

                    <h3>Choose Menu Items</h3>

                    {% for item in menu_items %}
                        <div class="menu-row">
                            <div>
                                <strong>{{ item.name }}</strong><br>
                                ${{ "%.2f"|format(item.price) }}<br>
                                <small>{{ item.description or "" }}</small>
                            </div>
                            <label>
                                Quantity
                                <input
                                    type="number"
                                    name="quantity_{{ item.item_id }}"
                                    min="0"
                                    value="0"
                                >
                            </label>
                        </div>
                    {% else %}
                        <p>No available menu items. Add some to the database first.</p>
                    {% endfor %}

                    <button type="submit">Create Order</button>
                </form>
            </section>

            <section>
                <h2>Order History</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Order</th>
                            <th>Date / Time</th>
                            <th>Customer</th>
                            <th>Table</th>
                            <th>Items</th>
                            <th>Total</th>
                            <th>Update Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for order in orders %}
                            <tr>
                                <td>#{{ order.order_id }}</td>
                                <td>{{ order.order_time }}</td>
                                <td>
                                    {% if order.first_name %}
                                        {{ order.first_name }} {{ order.last_name }}
                                    {% else %}
                                        Walk-in
                                    {% endif %}
                                </td>
                                <td>
                                    {% if order.table_number %}
                                        {{ order.table_number }}
                                    {% else %}
                                        Takeout / None
                                    {% endif %}
                                </td>
                                <td>{{ order.item_summary or "No items" }}</td>
                                <td>${{ "%.2f"|format(order.total) }}</td>
                                <td>{{ order.status|title }}</td>
                                <td>
                                    {% if order.status == 'pending' %}
                                        {% set next_statuses = ['preparing', 'cancelled'] %}
                                    {% elif order.status == 'preparing' %}
                                        {% set next_statuses = ['ready', 'cancelled'] %}
                                    {% elif order.status == 'ready' %}
                                        {% set next_statuses = ['completed', 'cancelled'] %}
                                    {% else %}
                                        {% set next_statuses = [] %}
                                    {% endif %}

                                    {% if next_statuses %}
                                        <form
                                            method="POST"
                                            action="{{ url_for(
                                                'update_order_status',
                                                order_id=order.order_id
                                            ) }}"
                                        >
                                            <select name="status" required>
                                                {% for status in next_statuses %}
                                                    <option value="{{ status }}">
                                                        {{ status|title }}
                                                    </option>
                                                {% endfor %}
                                            </select>
                                            <button type="submit">Update Status</button>
                                        </form>
                                    {% else %}
                                        <span>Final status</span>
                                    {% endif %}
                                </td>
                            </tr>
                        {% else %}
                            <tr><td colspan="8">No orders yet.</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </section>
        </main>
    </body>
    </html>
    """, customers=customers, tables=tables,
       menu_items=menu_items, orders=orders)


if __name__ == "__main__":
    app.run(debug=True)
