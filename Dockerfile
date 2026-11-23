# ParkControl en un solo contenedor: Django sirve la API y el build de Angular.

# 1. Build de Angular
FROM node:22-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npx ng build

# 2. Django + gunicorn
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_DEBUG=0 \
    FRONTEND_DIST=/app/frontend
WORKDIR /app/backend
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
COPY --from=frontend /app/frontend/dist/frontend/browser /app/frontend
RUN DJANGO_SECRET_KEY=solo-para-collectstatic python manage.py collectstatic --noinput
EXPOSE 8000
CMD ["sh", "entrypoint.sh"]
