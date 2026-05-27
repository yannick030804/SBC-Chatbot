import sys
from pathlib import Path

from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import or_

SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from chatbot import get_user_library, process_user_message
from database import SessionLocal
from models import ChatMessage, ConversationState, User, create_tables

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-secret-key"
create_tables()


def build_default_history():
    return [
        {
            "role": "bot",
            "message": "Hello! I am your personal movie and series chatbot.",
        }
    ]


def get_chat_history(db, user_id):
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == user_id)
        .order_by(ChatMessage.id.asc())
        .all()
    )

    if not messages:
        return build_default_history()

    return [{"role": message.role, "message": message.message} for message in messages]


def save_chat_message(db, user_id, role, message):
    chat_message = ChatMessage(user_id=user_id, role=role, message=message)
    db.add(chat_message)
    db.commit()


@app.route("/", methods=["GET", "POST"])
def chat():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    db = SessionLocal()

    try:
        history = get_chat_history(db, user_id)
        library = get_user_library(db, user_id)

        if request.method == "POST":
            user_message = request.form.get("message", "").strip()
            if user_message:
                save_chat_message(db, user_id, "user", user_message)
                bot_message = process_user_message(user_message, db=db, user_id=user_id)
                save_chat_message(db, user_id, "bot", bot_message)
            return redirect(url_for("chat"))

        return render_template(
            "chat.html",
            history=history,
            library=library,
            username=session.get("username"),
        )
    finally:
        db.close()


@app.post("/reset")
def reset_chat():
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = SessionLocal()
    try:
        db.query(ChatMessage).filter(ChatMessage.user_id == session["user_id"]).delete()
        db.query(ConversationState).filter(
            ConversationState.user_id == session["user_id"]
        ).delete()
        db.commit()
    finally:
        db.close()

    return redirect(url_for("chat"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("chat"))

    error = None

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
                    return redirect(url_for("login"))
            finally:
                db.close()

    return render_template("register.html", error=error)


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
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
