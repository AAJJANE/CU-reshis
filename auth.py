"""Пользователи: хранение в SQLite, регистрация и проверка пароля."""
import re
import sqlite3
from pathlib import Path

from werkzeug.security import check_password_hash, generate_password_hash

DB_PATH = Path(__file__).parent / "data" / "users.db"
USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,30}$")   # латиница, цифры и _, от 3 до 30 символов


def _connect():
    return sqlite3.connect(DB_PATH)


def init_db():
    """Создаёт таблицу пользователей, если её ещё нет."""
    with _connect() as db:
        db.execute(
            """CREATE TABLE IF NOT EXISTS users (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   username TEXT UNIQUE NOT NULL,
                   password_hash TEXT NOT NULL
               )"""
        )


def register(username, password, password2):
    """Регистрирует пользователя. Возвращает текст ошибки или None, если всё хорошо."""
    if not USERNAME_RE.match(username):
        return "Логин: от 3 до 30 символов, только латинские буквы, цифры и _"
    if len(password) < 6:
        return "Пароль должен быть не короче 6 символов"
    if password != password2:
        return "Пароли не совпадают"

    # В базе хранится не сам пароль, а его хэш: даже если базу украдут, паролей там не будет
    try:
        with _connect() as db:
            db.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, generate_password_hash(password)),
            )
    except sqlite3.IntegrityError:
        return "Пользователь с таким логином уже есть"
    return None


def check_login(username, password):
    """True, если логин существует и пароль верный."""
    with _connect() as db:
        row = db.execute("SELECT password_hash FROM users WHERE username = ?", (username,)).fetchone()
    return row is not None and check_password_hash(row[0], password)
