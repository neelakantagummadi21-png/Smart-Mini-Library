from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from config import Config
from models.book import Book
from models.user import db, User

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        if User.query.filter_by(email=email).first():
            flash("Email already exists!")
            return redirect(url_for("register"))

        user = User(
            name=name,
            email=email,
            role="user"
        )

        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash("Registration Successful!")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        # Admin Login
        if email == "admin@library.com" and password == "Pass@2025":
            return redirect(url_for("admin_dashboard"))

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("dashboard"))

        flash("Invalid Credentials")

    return render_template("login.html")


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", user=current_user)
@app.route("/books")


@login_required
def books():

    all_books = Book.query.all()

    return render_template(
        "books.html",
        books=all_books
    )

@app.route("/add_book", methods=["GET", "POST"])
@login_required
def add_book():

    if request.method == "POST":

        title = request.form["title"]
        author = request.form["author"]
        category = request.form["category"]
        quantity = int(request.form["quantity"])

        book = Book(
            title=title,
            author=author,
            category=category,
            quantity=quantity,
            available=quantity
        )

        db.session.add(book)
        db.session.commit()

        flash("Book Added Successfully!")

        return redirect(url_for("books"))

    return render_template("add_book.html")


@app.route("/admin")
def admin_dashboard():
    return render_template("admin_dashboard.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)