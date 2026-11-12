// Логика страницы: отправляем форму на backend и показываем результат.
// Все расчёты делает сервер (forecast.py), здесь только отправка данных и отображение.

const form = document.getElementById("forecast-form");
const errorBox = document.getElementById("error");
const resultBox = document.getElementById("result");
let chart = null;   // график создаём один раз, потом только обновляем

// Красивый вывод чисел: 12 500 вместо 12500
const fmt = (x) => Math.round(x).toLocaleString("ru-RU");

form.addEventListener("submit", async (event) => {
    event.preventDefault();                                 // не перезагружать страницу

    // 1. Собираем данные формы
    const formData = new FormData(form);
    const request = {
        origin: formData.get("origin"),
        destination: formData.get("destination"),
        date: formData.get("date"),
        price: Number(formData.get("price")),
    };

    // 2. Отправляем их на backend
    const response = await fetch("/api/forecast", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(request),
    });
    // Если сессия закончилась — отправляем на страницу входа
    if (response.status === 401) {
        window.location.href = "/login";
        return;
    }
    const data = await response.json();

    // 3. Если сервер вернул ошибку — показываем её
    if (!response.ok) {
        errorBox.textContent = data.error;
        errorBox.hidden = false;
        resultBox.hidden = true;
        return;
    }
    errorBox.hidden = true;
    showResult(data);
});

function showResult(data) {
    const [year, month, day] = data.date.split("-");              // 2026-06-12 → 12.06.2026
    document.getElementById("result-title").textContent = `${data.name}, ${day}.${month}.${year}`;
    document.getElementById("seats").textContent = fmt(data.seats);
    document.getElementById("wants").textContent = fmt(Math.max(0, data.wants));
    document.getElementById("buys").textContent = fmt(data.buys);
    document.getElementById("buys-note").textContent =
        data.buys >= data.seats ? "самолёты заполнены полностью" : `свободно ${fmt(data.seats - data.buys)} мест`;
    document.getElementById("prices").textContent =
        `${fmt(data.base_price)} ₽ / ${fmt(data.recommended_price)} ₽`;
    document.getElementById("chart-price").textContent = `${fmt(data.price)} ₽`;
    resultBox.hidden = false;
    drawChart(data);
}

function drawChart(data) {
    const labels = data.scenarios.map((s) => `${Math.round(s.quantile * 100)}%`);
    const wants = data.scenarios.map((s) => Math.max(0, s.wants));   // спрос не бывает отрицательным
    const colors = data.scenarios.map((s) => (s.quantile === "0.5" ? "#16325c" : "#8fb3e8"));

    const datasets = [
        {
            type: "bar",
            label: "Хотят купить при этой цене",
            data: wants,
            backgroundColor: colors,
        },
        {
            type: "line",
            label: "Мест в самолётах",
            data: data.scenarios.map(() => data.seats),
            borderColor: "#d93636",
            borderWidth: 2,
            pointRadius: 0,
        },
    ];

    if (chart) {                       // график уже есть — обновляем данные
        chart.data.labels = labels;
        chart.data.datasets = datasets;
        chart.update();
        return;
    }
    chart = new Chart(document.getElementById("chart"), {
        data: { labels, datasets },
        options: {
            locale: "ru-RU",           // числа на осях по-русски: 1 200 вместо 1,200
            scales: {
                x: { title: { display: true, text: "Сценарий прогноза (квантиль)" } },
                y: { beginAtZero: true, grace: "10%", title: { display: true, text: "Пассажиров" } },
            },
        },
    });
}
