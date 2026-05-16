"""75 Hard Tracker – Deutsche Web-App im Wikinger-Stil."""

import json
import os
from datetime import date, datetime, timedelta
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, url_for

app = Flask(__name__)

DATA_DIR = Path(os.environ.get("DATA_DIR", "data"))
DATA_FILE = DATA_DIR / "progress.json"

TASKS = ["workout1", "workout2", "diaet", "wasser", "lesen", "foto"]
MAX_FAILS = 3


def load_data() -> dict:
    """Lade den gespeicherten Fortschritt."""
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"start_date": None, "days": {}, "fails": 0, "fail_dates": []}


def save_data(data: dict) -> None:
    """Speichere den Fortschritt."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_current_day(data: dict) -> int:
    """Berechne den aktuellen Tag basierend auf dem Startdatum."""
    if not data.get("start_date"):
        return 0
    start = date.fromisoformat(data["start_date"])
    today = date.today()
    diff = (today - start).days + 1
    return min(max(diff, 1), 75)


def get_days_overview(data: dict) -> list:
    """Erstelle eine Übersicht aller 75 Tage für die Schlachtfeld-Ansicht."""
    if not data.get("start_date"):
        return []

    start = date.fromisoformat(data["start_date"])
    today = date.today()
    fail_dates = data.get("fail_dates", [])
    days = []

    for i in range(75):
        day_date = start + timedelta(days=i)
        day_str = day_date.isoformat()
        day_data = data.get("days", {}).get(day_str, {})

        if day_date > today:
            status = "future"
        elif day_str in fail_dates:
            status = "fail"
        elif all(day_data.get(t, False) for t in TASKS):
            status = "done"
        elif day_date == today:
            status = "today"
        else:
            # Vergangener Tag ohne alle Tasks = offen
            tasks_done = sum(1 for t in TASKS if day_data.get(t, False))
            status = "partial" if tasks_done > 0 else "missed"

        days.append({
            "number": i + 1,
            "date": day_str,
            "status": status,
        })

    return days


@app.route("/")
def index():
    """Hauptseite mit Tagesübersicht."""
    data = load_data()
    current_day = get_current_day(data)
    today_str = date.today().isoformat()
    today_data = data.get("days", {}).get(today_str, {})

    # Statistiken berechnen
    completed_days = 0
    for day_key, day_val in data.get("days", {}).items():
        if all(day_val.get(task, False) for task in TASKS):
            completed_days += 1

    fails = data.get("fails", 0)

    return render_template(
        "index.html",
        data=data,
        current_day=current_day,
        today_str=today_str,
        today_data=today_data,
        completed_days=completed_days,
        fails=fails,
        max_fails=MAX_FAILS,
        started=data.get("start_date") is not None,
    )


@app.route("/start", methods=["POST"])
def start_challenge():
    """Starte die 75 Hard Challenge."""
    data = load_data()
    data["start_date"] = date.today().isoformat()
    data["days"] = {}
    data["fails"] = 0
    data["fail_dates"] = []
    save_data(data)
    return redirect(url_for("index"))


@app.route("/reset", methods=["POST"])
def reset_challenge():
    """Challenge zurücksetzen (Neustart)."""
    data = {"start_date": None, "days": {}, "fails": 0, "fail_dates": []}
    save_data(data)
    return redirect(url_for("index"))


@app.route("/toggle", methods=["POST"])
def toggle_task():
    """Aufgabe als erledigt/nicht erledigt markieren."""
    task = request.form.get("task")
    day = request.form.get("day", date.today().isoformat())

    if task not in TASKS:
        return jsonify({"error": "Ungültige Aufgabe"}), 400

    data = load_data()
    if day not in data["days"]:
        data["days"][day] = {}

    current = data["days"][day].get(task, False)
    data["days"][day][task] = not current
    save_data(data)

    return redirect(url_for("index"))


@app.route("/fail", methods=["POST"])
def mark_fail():
    """Tag als Fail markieren. Nach 3 Fails wird zurückgesetzt."""
    day = request.form.get("day", date.today().isoformat())
    data = load_data()

    if "fail_dates" not in data:
        data["fail_dates"] = []
    if "fails" not in data:
        data["fails"] = 0

    if day not in data["fail_dates"]:
        data["fail_dates"].append(day)
        data["fails"] = len(data["fail_dates"])

    if data["fails"] >= MAX_FAILS:
        # Zurücksetzen nach 3 Fails
        data = {"start_date": None, "days": {}, "fails": 0, "fail_dates": []}
        save_data(data)
        return redirect(url_for("defeated"))

    save_data(data)
    return redirect(url_for("schlachtfeld"))


@app.route("/unfail", methods=["POST"])
def unmark_fail():
    """Fail-Markierung entfernen."""
    day = request.form.get("day")
    data = load_data()

    if day in data.get("fail_dates", []):
        data["fail_dates"].remove(day)
        data["fails"] = len(data["fail_dates"])

    save_data(data)
    return redirect(url_for("schlachtfeld"))


@app.route("/schlachtfeld")
def schlachtfeld():
    """Schlachtfeld-Ansicht: 75 Tage als Wikinger-Strichliste."""
    data = load_data()
    if not data.get("start_date"):
        return redirect(url_for("index"))

    days = get_days_overview(data)
    current_day = get_current_day(data)
    fails = data.get("fails", 0)

    return render_template(
        "schlachtfeld.html",
        days=days,
        current_day=current_day,
        fails=fails,
        max_fails=MAX_FAILS,
        data=data,
    )


@app.route("/defeated")
def defeated():
    """Niederlage-Seite nach 3 Fails."""
    return render_template("defeated.html")


@app.route("/history")
def history():
    """Verlauf aller Tage anzeigen."""
    data = load_data()
    if not data.get("start_date"):
        return redirect(url_for("index"))

    start = date.fromisoformat(data["start_date"])
    today = date.today()
    fail_dates = data.get("fail_dates", [])
    days_list = []

    for i in range(75):
        day_date = start + timedelta(days=i)
        if day_date > today:
            break
        day_str = day_date.isoformat()
        day_data = data.get("days", {}).get(day_str, {})
        tasks_done = sum(1 for t in TASKS if day_data.get(t, False))
        days_list.append({
            "date": day_str,
            "day_number": i + 1,
            "tasks_done": tasks_done,
            "complete": tasks_done == 6,
            "failed": day_str in fail_dates,
        })

    days_list.reverse()
    return render_template("history.html", days_list=days_list, data=data)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
