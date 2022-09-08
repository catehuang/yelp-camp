from flask import Flask, render_template, url_for, request, redirect
from flask_bootstrap import Bootstrap
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired, URL
from wtforms.widgets import TextArea

app = Flask("__name__")
app.config["SECRET_KEY"] = "ASQ2A@S!&(%&WR@34FT1251AS#^&@DGF"
Bootstrap(app)

year = datetime.now().year
PORT = 5000

# Connect to SQLite
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///campgrounds.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class Campground(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    image = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255), nullable=True)


db.create_all()


class CampgroundForm(FlaskForm):
    name = StringField("Campground Name", validators=[DataRequired()])
    image = StringField("Campground Image URL", validators=[DataRequired()])
    description = StringField("Campground Description", widget=TextArea(), validators=[DataRequired()])
    submit = SubmitField("Create")


@app.route('/landing')
def landing():
    return render_template("landing.html", year=year)


@app.route('/')
def home():
    campgrounds = db.session.query(Campground).all()
    return render_template("index.html", year=year, campgrounds=campgrounds)


@app.route('/new', methods=["GET", "POST"])
def new_campground():
    form = CampgroundForm()
    if form.validate_on_submit():
        new_campground = Campground(
            name=request.form["name"],
            image=request.form["image"],
            description=request.form["description"]
        )
        db.session.add(new_campground)
        db.session.commit()
        print({"Success": "Successfully create a new campground."})
        return redirect(url_for("home"))
    return render_template("new.html", year=year, form=form)


@app.route("/<int:campground_id>")
def show_campground(campground_id):
    total_campgrounds = db.session.query(Campground).count()
    campground = Campground.query.get(campground_id)
    return render_template("show.html", year=year, campground=campground, total=total_campgrounds)


@app.route("/edit", methods=["GET", "POST"])
def edit_campground():
    if request.method == "POST":
        campground_id = request.form["id"]
        target_campground = Campground.query.get(campground_id)
        target_campground.name = request.form["name"]
        target_campground.image = request.form["image"]
        target_campground.description = request.form["description"]
        db.session.commit()
    campground_id = request.args.get("id")
    selected_campground = Campground.query.get(campground_id)
    return render_template("show.html", campground=selected_campground)


@app.route("/delete")
def delete_campground():
    campground_id = request.args.get("id")
    target_campground = Campground.query.get(campground_id)
    db.session.delete(target_campground)
    db.session.commit()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(port=PORT, debug=True)