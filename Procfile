web: gunicorn crc_system.wsgi
release: python manage.py collectstatic --noinput && python manage.py migrate