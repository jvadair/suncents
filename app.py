from flask import Flask, render_template, request, redirect, url_for, jsonify, session, send_from_directory
from pyntree import Node
import sqlalchemy as db
from time import sleep
import re
from argon2 import PasswordHasher
from uuid import uuid4

app = Flask(__name__)
config = Node("config.yml")
ph = PasswordHasher()

# Regex
EMAIL_REGEX = re.compile(r"(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|\"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*\")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])", re.IGNORECASE)

# Server config
app.secret_key = config.flask.secret_key()

# DB config
dbsettings = config.db
while True:
    try:
        engine = db.create_engine(url="mysql+pymysql://{0}:{1}@{2}:{3}/{4}".format(  # me:password@host:port/db
                dbsettings.user(), dbsettings.password(), dbsettings.host(), dbsettings.port(), dbsettings.database()
            ))
        metadata = db.MetaData()
        conn = engine.connect()
        print("Database connection established!")
        break
    except Exception as e:
        print(e)
        print("Database connection failed, re-attemting in 30 seconds...")
        sleep(30)


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

    # Add user to DB
    users = db.Table("users", metadata, autoload_with=engine)
    q = db.insert(users)
    conn.execute(q, {
        "id": uuid4(),
        "username": username,
        "email": email,
        "password": ph.hash(password.encode("utf-8")),
        "verified": False,
        "verification_code": uuid4()
    })
    conn.commit()
    return redirect("/verify")


@app.route("/auth/login/", methods=["POST"])
def login():
    users = db.Table("users", metadata, autoload_with=engine)
    q = db.select(users).where(
        users.c.username == request.form.get("username")
    )
    user = conn.execute(q).fetchone()
    if not user:
        q = db.select([users]).where(
            users.c.email == request.form.get("username")
        )
        user = conn.execute(q).fetchone()
    if user:
        if ph.verify(user.password, request.form.get("password").encode("utf-8")):
            session["user_id"] = user.id
        else:
            return jsonify({"error": "Invalid password!"})
    else:
        return jsonify({"error": "Invalid username or email!"})
    return redirect("/")


if __name__ == "__main__":
    app.run(host=config.flask.host(), port=config.flask.port())
