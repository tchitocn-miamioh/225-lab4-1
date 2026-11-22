
from flask import (
    Flask,
    request,
    render_template_string,
    redirect,
    url_for
)
import sqlite3
import os
import re

app = Flask(__name__)

# Persistent SQLite database
DATABASE = os.environ.get("DATABASE_PATH", "/nfs/demo.db")


def get_db():
    db = sqlite3.connect(DATABASE, timeout=10)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    db = get_db()
    try:
        db.execute("""
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL
            )
        """)
        db.commit()
    finally:
        db.close()


def valid_name(name):
    return (
        bool(name)
        and len(name) <= 100
        and not any(ord(char) < 32 for char in name)
    )


def valid_phone(phone):
    if not re.fullmatch(r"[+0-9() .-]{7,30}", phone):
        return False

    digits = re.sub(r"\D", "", phone)
    return 7 <= len(digits) <= 15


@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "object-src 'none'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )
    return response


@app.route("/", methods=["GET", "POST"])
def index():

    if request.method == "POST":
        action = request.form.get("action", "add")

        if action == "delete":
            contact_id = request.form.get(
                "contact_id", ""
            ).strip()

            if not contact_id.isdigit() or int(contact_id) < 1:
                message = "Invalid contact ID."
            else:
                db = get_db()
                try:
                    cursor = db.execute(
                        "DELETE FROM contacts WHERE id = ?",
                        (int(contact_id),)
                    )
                    db.commit()

                    if cursor.rowcount:
                        message = "Contact deleted successfully."
                    else:
                        message = "Contact not found."
                finally:
                    db.close()

        elif action == "add":
            name = request.form.get(
                "name", ""
            ).strip()

            phone = request.form.get(
                "phone", ""
            ).strip()

            if not valid_name(name):
                message = "Invalid name."

            elif not valid_phone(phone):
                message = "Invalid phone number."

            else:
                db = get_db()
                try:
                    db.execute(
                        """
                        INSERT INTO contacts (name, phone)
                        VALUES (?, ?)
                        """,
                        (name, phone)
                    )
                    db.commit()
                    message = "Contact added successfully."
                finally:
                    db.close()

        else:
            message = "Invalid action."

        return redirect(
            url_for("index", message=message)
        )

    message = request.args.get("message", "")

    db = get_db()
    try:
        contacts = db.execute(
            "SELECT id, name, phone FROM contacts ORDER BY id"
        ).fetchall()
    finally:
        db.close()

    return render_template_string("""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport"
                  content="width=device-width, initial-scale=1">
            <title>Contacts</title>
        </head>
        <body>
            <h2>Add Contact</h2>

            <form method="POST"
                  action="{{ url_for('index') }}">

                <label for="name">Name:</label><br>
                <input type="text"
                       id="name"
                       name="name"
                       maxlength="100"
                       required><br>

                <label for="phone">Phone Number:</label><br>
                <input type="tel"
                       id="phone"
                       name="phone"
                       maxlength="30"
                       required><br><br>

                <input type="submit" value="Submit">
            </form>

            {% if message %}
                <p>{{ message }}</p>
            {% endif %}

            {% if contacts %}
                <table border="1"
                       cellpadding="6"
                       cellspacing="0">
                    <tr>
                        <th>Name</th>
                        <th>Phone Number</th>
                        <th>Delete</th>
                    </tr>

                    {% for contact in contacts %}
                    <tr>
                        <td>{{ contact['name'] }}</td>
                        <td>{{ contact['phone'] }}</td>
                        <td>
                            <form method="POST"
                                  action="{{ url_for('index') }}">
                                <input type="hidden"
                                       name="contact_id"
                                       value="{{ contact['id'] }}">
                                <input type="hidden"
                                       name="action"
                                       value="delete">
                                <input type="submit"
                                       value="Delete">
                            </form>
                        </td>
                    </tr>
                    {% endfor %}
                </table>
            {% else %}
                <p>No contacts found.</p>
            {% endif %}
        </body>
        </html>
    """, message=message, contacts=contacts)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    init_db()

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
