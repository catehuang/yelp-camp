from flask import Flask, render_template, url_for, request, redirect
from flask_bootstrap import Bootstrap
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_ckeditor import CKEditor, CKEditorField

app = Flask("__name__")
app.config["SECRET_KEY"] = "ASQ2A@S!&(%&WR@34FT1251AS#^&@DGF"
Bootstrap(app)
ckeditor = CKEditor(app)

now = datetime.now()
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
    postedDate = db.Column(db.Date, nullable=True)

db.create_all()


class CampgroundForm(FlaskForm):
    name = StringField("Campground Name", validators=[DataRequired()])
    image = StringField("Campground Image URL", validators=[DataRequired()])
    description = CKEditorField("Campground Description", validators=[DataRequired()])
    submit = SubmitField("Submit")


@app.route('/landing')
def landing():
    return render_template("landing.html", now=now)


@app.route('/')
def home():
    campgrounds = db.session.query(Campground).all()
    return render_template("index.html", now=now, campgrounds=campgrounds)


@app.route('/new', methods=["GET", "POST"])
def new_campground():
    form = CampgroundForm()
    if form.validate_on_submit():
        new_campground = Campground(
            name=request.name.data,
            image=request.image.data,
            description=request.description.data,
            postedDate=now
        )
        db.session.add(new_campground)
        db.session.commit()
        # print({"Success": "Successfully create a new campground."})
        return redirect(url_for("home"))
    return render_template("new.html", now=now, form=form)


@app.route("/<int:campground_id>")
def show_campground(campground_id):
    total_campgrounds = db.session.query(Campground).count()
    campground = Campground.query.get(campground_id)
    return render_template("show.html", now=now, campground=campground, total=total_campgrounds)


@app.route("/edit/<int:campground_id>", methods=["GET", "POST"])
def edit_campground(campground_id):
    total_campgrounds = db.session.query(Campground).count()
    # Retrieve data from database and fill form
    original_campground = Campground.query.get(campground_id)
    edit_campground = CampgroundForm(
        name=original_campground.name,
        image=original_campground.image,
        description=original_campground.description,
        postedDate=now
    )
    # Store data which was edited by a user
    if edit_campground.validate_on_submit():
        original_campground.name = edit_campground.name.data
        original_campground.image = edit_campground.image.data
        original_campground.description = edit_campground.description.data
        original_campground.postedDate = now
        db.session.commit()
        return redirect(url_for("show_campground", campground_id=campground_id, now=now, total=total_campgrounds))
    return render_template("new.html", form=edit_campground, now=now, id=campground_id, is_edit=True)


@app.route("/delete/<int:campground_id>")
def delete_campground(campground_id):
    target_campground = Campground.query.get(campground_id)
    db.session.delete(target_campground)
    db.session.commit()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(port=PORT, debug=True)