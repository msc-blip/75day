# 75 Hard Tracker 🇩🇪

Eine deutsche Web-App zum Tracken der 75 Hard Challenge – läuft im Docker-Container.

## Die Regeln

Jeden Tag für 75 Tage:

- 🏋️ 2 Workouts à 45 Minuten (eines davon draußen)
- 🥗 Diät einhalten – kein Alkohol, keine Cheat Meals
- 💧 4 Liter Wasser trinken
- 📖 10 Seiten Sachbuch lesen
- 📸 Fortschrittsfoto machen

## Starten

```bash
docker compose up -d
```

Die App ist dann unter **http://localhost:5000** erreichbar.

## Entwicklung (ohne Docker)

```bash
pip install -r requirements.txt
python app.py
```

## Daten

Der Fortschritt wird als JSON in `data/progress.json` gespeichert. Das Volume ist gemountet, sodass die Daten auch nach Container-Neustart erhalten bleiben.
