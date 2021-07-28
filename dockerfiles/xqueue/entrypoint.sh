#!/bin/sh

export DJANGO_SETTINGS_MODULE=xqueue.production

./manage.py migrate
./manage.py update_users
gunicorn -c /edx/app/xqueue/xqueue/docker_gunicorn_configuration.py --bind=0.0.0.0:8040 --workers 2 --max-requests=1000 xqueue.wsgi:application

