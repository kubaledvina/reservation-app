import os
import ssl
import sqlite3
import smtplib
from email.mime.text import MIMEText
from flask import Flask, request, render_template
from flask.cli import load_dotenv

app = Flask(__name__)

# connect to db
def init_db():
    conn = sqlite3.connect("reservations.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT  NULL,
            email TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def send_email(to_email, name, date, time):
    load_dotenv("mail_password.env")
    password = os.environ.get("MAIL_PASSWORD")

    subject = "Reservation confirmation!"
    body = (f"Hi {name},\nYour reservation has been accepted. When {date} {time}\n\nWe look forward to seeing you.")

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = "your_email"
    msg["To"] = to_email

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login("your_email", password)
        server.send_message(msg)



@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        date = request.form["date"]
        time = request.form["time"]

        conn = sqlite3.connect("reservations.db")
        c = conn.cursor()

        c.execute("SELECT * FROM reservations WHERE date=? AND time=?", (date, time))
        conflict = c.fetchone()

        if conflict:
            conn.close()
            return render_template("index.html", message="This date is already booked!")

        c.execute("INSERT INTO reservations (name, email, date, time) VALUES (?, ?, ?, ?)",
                  (name, email, date, time))
        conn.commit()
        conn.close()

        try:
            send_email(email, name, date, time)
        except Exception as e:
            print("Error send email:", e)

        return render_template("index.html", message=f"Reservation on {date} v {time}.", send_info=f"Send email on {email}")

    return render_template("index.html")

@app.route("/admin")
def admin():
    conn = sqlite3.connect("reservations.db")
    c = conn.cursor()
    c.execute("SELECT * FROM reservations")
    reservations = c.fetchall()
    conn.close()
    return render_template("admin.html", reservations=reservations)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)