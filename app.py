"""Веб-приложение «Решись Авиа»: прогноз продаж билетов по маршруту, дате и цене."""
import os
import secrets
from functools import wraps
from pathlib import Path

from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for

import auth
import forecast

app = Flask(__name__)


def load_secret_key():
    """Секретный ключ подписывает cookie сессии. Создаём его один раз и храним в файле."""
    key_file = Path(__file__).parent / "data" / "secret_key.txt"
    if not key_file.exists():
        key_file.write_text(secrets.token_hex(32))
    return key_file.read_text().strip()


app.secret_key = os.environ.get("SECRET_KEY") or load_secret_key()
auth.init_db()


def login_required(view):
    """Декоратор: пускает на страницу только вошедших пользователей."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "username" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"error": "Нужно войти в аккаунт"}), 401
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapper


# ---------- Регистрация, вход, выход ----------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        error = auth.register(username, request.form.get("password", ""), request.form.get("password2", ""))
        if error:
            flash(error)
            return render_template("register.html", username=username)
        session["username"] = username          # сразу входим после регистрации
        return redirect(url_for("index"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        if auth.check_login(username, request.form.get("password", "")):
            session["username"] = username
            return redirect(url_for("index"))
        flash("Неверный логин или пароль")
        return render_template("login.html", username=username)
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------- Прогноз ----------

@app.route("/")
@login_required
def index():
    """Главная страница с формой."""
    origins, destinations = forecast.get_cities()
    first_date, last_date = forecast.get_dates()
    return render_template(
        "index.html",
        origins=origins,
        destinations=destinations,
        first_date=first_date,
        last_date=last_date,
    )


@app.route("/api/forecast", methods=["POST"])
@login_required
def api_forecast():
    """API: принимает JSON {origin, destination, date, price}, возвращает прогноз."""
    data = request.get_json(silent=True) or {}
    try:
        price = float(data.get("price", ""))
    except (TypeError, ValueError):
        return jsonify({"error": "Цена должна быть числом"}), 400

    try:
        result = forecast.predict(
            origin=data.get("origin", ""),
            destination=data.get("destination", ""),
            date=data.get("date", ""),
            price=price,
        )
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)
