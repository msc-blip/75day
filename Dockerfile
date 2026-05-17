FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data

ENV PORT=5000

EXPOSE ${PORT}

CMD gunicorn --bind 0.0.0.0:${PORT} --log-level warning app:app
