
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

COPY templates/ templates/

COPY static/ static/

RUN mkdir -p /app/data

ENV PYTHONUNBUFFERED=1
ENV DATABASE=/app/data/threatwatch.db

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
