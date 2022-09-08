from functools import wraps
from flask import Flask, render_template, url_for, request, redirect, abort
from flask_bootstrap import Bootstrap
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_ckeditor import CKEditor, CKEditorField
from forms import CampgroundForm, RegisterForm, LoginForm
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user


app = Flask("__name__")
app.config["SECRET_KEY"] = "ASQ2A@S!&(%&WR@34FT1251AS#^&@DGF"
Bootstrap(app)
ckeditor = CKEditor(app)

now = datetime.now()
PORT = 5000

# Connect to SQLite
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///yelpCamp.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    posts = relationship("Campground", back_populates="author")


class Campground(db.Model):
    __tablename__ = "campgrounds"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    image = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")
    postedDate = db.Column(db.Date, nullable=True)


db.create_all()


def admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            print("This email has been registered.")
            return redirect(url_for("register"))
        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            name=form.name.data,
            email=form.email.data,
            password=hash_and_salted_password
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        print("Register successfully.")
        return render_template(url_for("home"))
    return render_template("register.html", now=now, form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    return render_template("login.html", now=now, form=form)


@app.route("/logout")
def logout():
    return redirect("home", now=now)


@app.route('/')
def landing():
    return render_template("landing.html", now=now)


@app.route('/index')
def home():
    campgrounds = Campground.query.all()
    return render_template("index.html", now=now, campgrounds=campgrounds, current_user=current_user)


@app.route('/new', methods=["GET", "POST"])
def new_campground():
    form = CampgroundForm()
    if form.validate_on_submit():
        new_campground = Campground(
            name=request.form.get("name"),
            image=request.form.get("image"),
            description=request.form.get("description"),
            postedDate=now,
            author=current_user
        )
        db.session.add(new_campground)
        db.session.commit()
        # print({"Success": "Successfully create a new campground."})
        return redirect(url_for("home"))
    return render_template("new.html", now=now, form=form, current_user=current_user)


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
        postedDate=now,
        author=current_user
    )
    # Store data which was edited by a user
    if edit_campground.validate_on_submit():
        original_campground.name = edit_campground.name.data
        original_campground.image = edit_campground.image.data
        original_campground.description = edit_campground.description.data
        original_campground.postedDate = now
        db.session.commit()
        return redirect(url_for("show_campground", campground_id=campground_id, now=now, total=total_campgrounds))
    return render_template("new.html", form=edit_campground, now=now, id=campground_id, is_edit=True,
                           current_user=current_user)


@app.route("/delete/<int:campground_id>")
def delete_campground(campground_id):
    target_campground = Campground.query.get(campground_id)
    db.session.delete(target_campground)
    db.session.commit()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(port=PORT, debug=True)