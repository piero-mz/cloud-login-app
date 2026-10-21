# Imagen propia de la aplicación web (Flask + Gunicorn)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/app.py .
COPY app/templates/ templates/
COPY app/static/ static/
# El script de BD va dentro de la imagen para poder inicializar la BD administrada (Opción A)
COPY db/init.sql .

# Usuario sin privilegios (no correr como root)
RUN useradd --create-home appuser
USER appuser

EXPOSE 8000
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT} --workers 2 --access-logfile - app:app"]
