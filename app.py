from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from pyntree import Node

app = Flask(__name__)
config = Node("config.yml")


@app.route("/")
def index():
    return render_template("index.html")


@app.route('/fonts')
def get_font_url():
    formatted_font_list = '&family='.join(config.fonts())
    target = f"https://fonts.googleapis.com/css2?family={formatted_font_list}&display=swap"
    return redirect(target)


if __name__ == "__main__":
    app.run()
