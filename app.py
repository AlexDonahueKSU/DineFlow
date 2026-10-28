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
            <p>Restaurant Management Dashboard</p>
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

if __name__ == "__main__":
    app.run(debug=True)
