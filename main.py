from flask import Flask, render_template, url_for
from flask_bootstrap import Bootstrap
from _datetime import datetime

app = Flask("__name__")
Bootstrap(app)


@app.route('/')
def landing():
    return render_template("landing.html")


@app.route('/campgrounds')
def home():
    return render_template("index.html")



if __name__ == "__main__":
    app.run(debug=True)