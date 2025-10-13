#!/bin/sh

# helper to develop this package by running django commands inside a virtualenv

# usage : django-admin DJANGO_CMD
# ex:
#       django-admin.sh runserver
#       django-admin.sh shell
#       django-admin.sh makemigrations wagtail_parler

export DJANGO_SETTINGS_MODULE="wagtail_parler_tests.settings"
export DATABASE_NAME="wagtail_parler.sqlite"

if [ ! -d ./.venv ] ; then
    python -m venv ./.venv
    . ./.venv/bin/activate
    pip install -e ./
    pip install wagtail-modeladmin
    django-admin createcachetable
    django-admin migrate
else
    . ./.venv/bin/activate
fi

django-admin $@

deactivate
