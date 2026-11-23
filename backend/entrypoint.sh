#!/bin/sh
# Arranque del contenedor: migra la base, opcionalmente carga los datos de prueba y levanta gunicorn.
set -e

python manage.py migrate --noinput

if [ "$CARGAR_DATOS_INICIALES" = "1" ]; then
  # Idempotente: no duplica nada si ya están cargados
  python manage.py cargar_datos_iniciales
fi

exec gunicorn parkcontrol.wsgi:application \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers "${WEB_CONCURRENCY:-3}" \
  --access-logfile -
