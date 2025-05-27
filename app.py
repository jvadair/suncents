import argon2.exceptions
from flask import Flask, render_template, request, redirect, url_for, jsonify, session, send_from_directory
from pyntree import Node
from time import sleep
import re
from argon2 import PasswordHasher
import uuid

from rich.markup import render

from db_connector import db, conn, engine, metadata
from sendmail import send_template

app = Flask(__name__)
config = Node("config.yml")
ph = PasswordHasher()

# Regex
EMAIL_REGEX = re.compile(r"(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|\"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*\")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])", re.IGNORECASE)

# Server config
app.secret_key = config.flask.secret_key()


@app.route("/")
def index():
    return render_template("index.html")


@app.route('/fonts')
def get_font_url():
    formatted_font_list = '&family='.join(config.fonts())
    target = f"https://fonts.googleapis.com/css2?family={formatted_font_list}&display=swap"
    return redirect(target)


# @app.route('/static/<path:path>')
# def static_file(path):
#     return send_from_directory('static', path)


@app.route("/auth/<action>/", methods=["GET"])
def auth(action):
    if action == "login":
        return render_template("auth.html", auth_type="login")
    elif action == "register":
        return render_template("auth.html", auth_type="register")
    else:
        return 404


@app.route("/auth/register/", methods=["POST"])
def register():
    email = request.form.get("email")
    username = request.form.get("username")
    password = request.form.get("password")
    if not (email and username and password):
        return jsonify({"error": "All fields are required!"})
    if not EMAIL_REGEX.match(email):
        return jsonify({"error": "Invalid email!"})

    # Validate that email and username are not taken
    users = db.Table("users", metadata, autoload_with=engine)
    email_exists = db.select(users).where(
        users.c.email == email
    )
    username_exists = db.select(users).where(
        users.c.username == username
    )
    if conn.execute(email_exists).fetchone():
        return jsonify({"error": "Email already exists!"})
    if conn.execute(username_exists).fetchone():
        return jsonify({"error": "Username already exists!"})

    # Add user to database
    q = db.insert(users).returning(users)
    result = conn.execute(q, {
        "username": username,
        "email": email,
        "password": ph.hash(password.encode("utf-8")),
    })
    conn.commit()
    user = result.fetchone()
    send_template("email/verify.html", "Verify your Suncents account", email, ignore_unsubscribed=True, verification_code=user.verification_code)
    return redirect("/verify")


@app.route("/auth/login/", methods=["POST"])
def login():
    users = db.Table("users", metadata, autoload_with=engine)
    q = db.select(users).where(
        users.c.username == request.form.get("username")
    )
    user = conn.execute(q).fetchone()
    if not user:
        q = db.select(users).where(
            users.c.email == request.form.get("username")
        )
        user = conn.execute(q).fetchone()
    if user:
        try:
            ph.verify(user.password, request.form.get("password").encode("utf-8"))
            session["user_id"] = user.id
            session["verified"] = user.verified
        except argon2.exceptions.VerifyMismatchError:
            return jsonify({"error": "Invalid password!"})
    else:
        return jsonify({"error": "Invalid username or email!"})
    return redirect("/")


@app.route('/logout/')
def logout():
    session.pop("user_id", None)
    return redirect("/")


@app.route("/verify/", methods=["GET"])
def verify():
    token = request.args.get("token")
    if not token:
        return render_template("verify.html")
    users = db.Table("users", metadata, autoload_with=engine)
    q = db.select(users).where(
        users.c.verification_code == uuid.UUID(token)
    )
    user = conn.execute(q).fetchone()
    if user:
        q = db.update(users).where(
            users.c.id == user.id
        )
        conn.execute(q, {"verified": True})
        conn.commit()
        if session.get("verified"):  # If the user is logged in
            session["verified"] = True
    else:
        return jsonify({"error": "Invalid verification code!"})
    return redirect("/")


@app.route("/verify", methods=["POST"])
def doublecheck_verify():
    if not session.get("user_id"):
        return redirect("/auth/login")
    users = db.Table("users", metadata, autoload_with=engine)
    q = db.select(users).where(
        users.c.id == session.get("user_id")
    )
    user = conn.execute(q).fetchone()
    if user.verified:
        session["verified"] = True
        return redirect("/")
    return render_template("verify.html")


@app.before_request
def before_request():
    if (request.path.split("/")[1] != "verify"
            and not request.path.startswith("/static"))\
            and not request.path.split("/")[1] == "logout"\
            and not request.path == "/fonts":
        if session.get("user_id"):
            if not session.get("verified"):
                return redirect("/verify")


@app.context_processor
def context_processor():
    users = db.Table("users", metadata, autoload_with=engine)
    bal = lambda: conn.execute(db.select(users).where(users.c.id == session.get("user_id"))).fetchone().balance
    return {
        "bal": bal,
    }

if __name__ == "__main__":
    app.run(host=config.flask.host(), port=config.flask.port())
