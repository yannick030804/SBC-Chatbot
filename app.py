import sys
from pathlib import Path

from flask import Flask, redirect, render_template, request, session, url_for

SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from chatbot import process_user_message

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
    history = get_chat_history()

    if request.method == "POST":
        user_message = request.form.get("message", "").strip()
        if user_message:
            history.append({"role": "user", "message": user_message})
            bot_message = process_user_message(user_message)
            history.append({"role": "bot", "message": bot_message})
            session["chat_history"] = history
        return redirect(url_for("chat"))

    return render_template("chat.html", history=history)


@app.post("/reset")
def reset_chat():
    session.pop("chat_history", None)
    return redirect(url_for("chat"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
