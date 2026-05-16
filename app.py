"""75 Hard Tracker – Deutsche Web-App."""

import json
import os
from datetime import date, datetime, timedelta
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, url_for

app = Flask(__name__)

DATA_DIR = Path(os.environ.get("DATA_DIR", "data"))
DATA_FILE = DATA_DIR / "progress.json"


def load_data() -> dict:
    """Lade den gespeicherten Fortschritt."""
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"start_date": None, "days": {}}


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
        if all(day_val.get(task, False) for task in [
            "workout1", "workout2", "diaet", "wasser", "lesen", "foto"
        ]):
            completed_days += 1

    return render_template(
        "index.html",
        data=data,
        current_day=current_day,
        today_str=today_str,
        today_data=today_data,
        completed_days=completed_days,
        started=data.get("start_date") is not None,
    )


@app.route("/start", methods=["POST"])
def start_challenge():
    """Starte die 75 Hard Challenge."""
    data = load_data()
    data["start_date"] = date.today().isoformat()
    data["days"] = {}
    save_data(data)
    return redirect(url_for("index"))


@app.route("/reset", methods=["POST"])
def reset_challenge():
    """Challenge zurücksetzen (Neustart)."""
    data = {"start_date": None, "days": {}}
    save_data(data)
    return redirect(url_for("index"))


@app.route("/toggle", methods=["POST"])
def toggle_task():
    """Aufgabe als erledigt/nicht erledigt markieren."""
    task = request.form.get("task")
    day = request.form.get("day", date.today().isoformat())

    valid_tasks = ["workout1", "workout2", "diaet", "wasser", "lesen", "foto"]
    if task not in valid_tasks:
        return jsonify({"error": "Ungültige Aufgabe"}), 400

    data = load_data()
    if day not in data["days"]:
        data["days"][day] = {}

    current = data["days"][day].get(task, False)
    data["days"][day][task] = not current
    save_data(data)

    return redirect(url_for("index"))


@app.route("/history")
def history():
    """Verlauf aller Tage anzeigen."""
    data = load_data()
    if not data.get("start_date"):
        return redirect(url_for("index"))

    start = date.fromisoformat(data["start_date"])
    today = date.today()
    days_list = []

    for i in range(75):
        day_date = start + timedelta(days=i)
        if day_date > today:
            break
        day_str = day_date.isoformat()
        day_data = data.get("days", {}).get(day_str, {})
        tasks_done = sum(1 for t in ["workout1", "workout2", "diaet", "wasser", "lesen", "foto"] if day_data.get(t, False))
        days_list.append({
            "date": day_str,
            "day_number": i + 1,
            "tasks_done": tasks_done,
            "complete": tasks_done == 6,
        })

    days_list.reverse()
    return render_template("history.html", days_list=days_list, data=data)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
