"""Расчёт прогноза продаж по файлу прогноза спроса (my_forecast.csv) и параметрам маршрутов (routes.csv)."""
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent / "data"
FORECAST_FILE = "Arshinova_Evgeniya_Aleksandrovna_my_forecast.csv"   # мой прогноз из ML-части (задание 7 ноутбука)
QUANTILES = ["0.1", "0.2", "0.3", "0.4", "0.5", "0.6", "0.7", "0.8", "0.9"]

# Загружаем данные один раз при запуске приложения
routes = pd.read_csv(DATA_DIR / "routes.csv")
forecast = pd.read_csv(DATA_DIR / FORECAST_FILE, dtype={"date": str})

# Название маршрута "Москва — Сочи" делим на пункт отправления и пункт назначения
routes["origin"] = routes["name"].str.split(" — ").str[0]
routes["destination"] = routes["name"].str.split(" — ").str[1]


def get_cities():
    """Списки городов для формы: откуда и куда."""
    return sorted(routes["origin"].unique()), sorted(routes["destination"].unique())


def get_dates():
    """Первая и последняя дата, на которые есть прогноз."""
    return forecast["date"].min(), forecast["date"].max()


def predict(origin, destination, date, price):
    """Прогноз продаж для рейса при заданной цене.

    Возвращает словарь с результатом или выбрасывает ValueError с понятным текстом ошибки.
    """
    route = routes[(routes["origin"] == origin) & (routes["destination"] == destination)]
    if route.empty:
        raise ValueError(f"Рейсов из «{origin}» в «{destination}» нет")
    route = route.iloc[0]

    row = forecast[(forecast["route"] == route["route"]) & (forecast["date"] == date)]
    if row.empty:
        first, last = get_dates()
        raise ValueError(f"Нет прогноза на {date}: доступны даты с {first} по {last}")
    row = row.iloc[0]

    if price <= 0:
        raise ValueError("Цена должна быть больше нуля")

    seats = int(row["seats"])
    sensitivity = route["price_sensitivity"]
    base_price = route["base_price"]

    def wants_at_price(base_demand):
        """Формула из задания: сколько человек захотят купить билет при введённой цене."""
        return base_demand - sensitivity * (price - base_price)

    def buys(wants):
        """Продажи не бывают отрицательными и не превышают число мест."""
        return min(seats, max(0, wants))

    # Простой прогноз: по медиане 0.5_base_demand
    wants = wants_at_price(row["0.5_base_demand"])

    # 9 сценариев для графика: та же формула, но со своим base_demand
    scenarios = []
    for q in QUANTILES:
        w = wants_at_price(row[f"{q}_base_demand"])
        scenarios.append({"quantile": q, "wants": round(w, 1), "buys": round(buys(w), 1)})

    return {
        "route": route["route"],
        "name": route["name"],
        "date": date,
        "price": price,
        "base_price": int(base_price),
        "seats": seats,
        "wants": round(wants, 1),
        "buys": round(buys(wants), 1),
        "recommended_price": int(row["0.5_price"]),   # лучшая цена для медианного сценария из ML-части
        "scenarios": scenarios,
    }
