from functools import wraps
from flask import Flask, render_template, url_for, request, redirect, abort, flash
from flask_bootstrap import Bootstrap
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from flask_ckeditor import CKEditor
from forms import CampgroundForm, RegisterForm, LoginForm
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
import os

app = Flask("__name__")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
Bootstrap(app)
ckeditor = CKEditor(app)

now = datetime.now()
PORT = 5000

# Connect to SQLite
# app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///yelpCamp.db"
env_postgres = os.environ.get("DATABASE_URL")
if env_postgres.startswith("postgres://"):
    env_postgres = env_postgres.replace("postgres://", "postgresql://")
app.config["SQLALCHEMY_DATABASE_URI"] = env_postgres

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
    error = None
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            error = "This email has been registered. Please try again."
        else:
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
            # flash("Register successfully.")
            return redirect(url_for("home"))
    return render_template("register.html", now=now, form=form, error=error)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    error = None
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = User.query.filter_by(email=email).first()
        if not user:
            error = "Email or password incorrect. Please try again."
        elif not check_password_hash(user.password, password):
            error = "Email or password incorrect. Please try again."
        else:
            login_user(user)
            # flash("Logged in successfully.")
            return redirect(url_for("home"))
    return render_template("login.html", now=now, form=form, current_user=current_user, error=error)


@app.route("/user/<user_id>")
def user_account(user_id):
    error = None
    if current_user.is_authenticated:
        if int(user_id) == int(current_user.id):
            campgrounds = Campground.query.filter_by(author_id=current_user.id)
            return render_template("user.html", now=now, current_user=current_user, campgrounds=campgrounds)
        else:
            error = "Permission denied."
    else:
        error = "Permission denied. Please login first."

    return redirect(url_for("home"))


@app.route("/logout")
def logout():
    logout_user()
    flash("Logout successfully.")
    return redirect(url_for("home"))


@app.route('/')
def landing():
    return render_template("landing.html", now=now)


@app.route('/index')
def home():
    campgrounds = Campground.query.all()
    return render_template("index.html", now=now, campgrounds=campgrounds, current_user=current_user)


@app.route('/new', methods=["GET", "POST"])
def new_campground():
    if current_user.is_authenticated:
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
    else:
        return redirect(url_for("home"))


@app.route("/<int:campground_id>")
def show_campground(campground_id):
    campground = Campground.query.get(campground_id)
    campgrounds = Campground.query.all()
    index = campgrounds.index(campground)
    return render_template("show.html", now=now, campground=campground, index=index, total=len(campgrounds))


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
    app.run(host='0.0.0.0', port=PORT)