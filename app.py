import sys
from pathlib import Path

from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import or_

SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from chatbot import process_user_message
from database import SessionLocal
from models import User

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-secret-key"


def get_chat_history():
    if "chat_history" not in session:
        session["chat_history"] = [
            {
                "role": "bot",
                "message": ("Hello! I am your personal movie and series chatbot."),
            }
        ]
    return session["chat_history"]


@app.route("/", methods=["GET", "POST"])
def chat():
    if "user_id" not in session:
        return redirect(url_for("login"))

    history = get_chat_history()

    if request.method == "POST":
        user_message = request.form.get("message", "").strip()
        if user_message:
            history.append({"role": "user", "message": user_message})
            bot_message = process_user_message(user_message)
            history.append({"role": "bot", "message": bot_message})
            session["chat_history"] = history
        return redirect(url_for("chat"))

    return render_template(
        "chat.html",
        history=history,
        username=session.get("username"),
    )


@app.post("/reset")
def reset_chat():
    session.pop("chat_history", None)
    return redirect(url_for("chat"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("chat"))

    error = None
    success = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not username or not email or not password:
            error = "Please fill in username, email, and password."
        elif len(password) < 6:
            error = "Password must be at least 6 characters long."
        else:
            db = SessionLocal()
            try:
                existing_user = (
                    db.query(User)
                    .filter(or_(User.username == username, User.email == email))
                    .first()
                )

                if existing_user:
                    error = "That username or email already exists."
                else:
                    user = User(
                        username=username,
                        email=email,
                        password_hash=generate_password_hash(password),
                    )
                    db.add(user)
                    db.commit()
                    db.refresh(user)

                    session["user_id"] = user.id
                    session["username"] = user.username
                    success = "User created successfully."
            finally:
                db.close()

    return render_template("register.html", error=error, success=success)


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("chat"))

    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            error = "Please fill in username and password."
        else:
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.username == username).first()

                if user is None or not check_password_hash(user.password_hash, password):
                    error = "Invalid username or password."
                else:
                    session["user_id"] = user.id
                    session["username"] = user.username
                    return redirect(url_for("chat"))
            finally:
                db.close()

    return render_template("login.html", error=error)


@app.get("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("username", None)
    session.pop("chat_history", None)
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
