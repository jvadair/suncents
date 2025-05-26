from flask import Flask, render_template, request, redirect, url_for, jsonify, session, send_from_directory
from pyntree import Node
import sqlalchemy as db
from time import sleep

app = Flask(__name__)
config = Node("config.yml")

# DB config
dbsettings = config.db
while True:
    try:
        db.create_engine(url="mysql+pymysql://{0}:{1}@{2}:{3}/{4}".format(  # me:password@host:port/db
                dbsettings.user(), dbsettings.password(), dbsettings.host(), dbsettings.port(), dbsettings.database()
            ))
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


if __name__ == "__main__":
    app.run()
