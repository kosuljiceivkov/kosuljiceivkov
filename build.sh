#!/usr/bin/env bash
# Render.com build — ista codebase, production settings (PostgreSQL + R2)
set -o errexit
set -o pipefail

echo "==> Installing dependencies"
pip install --upgrade pip
pip install -r requirements.txt

export DJANGO_SETTINGS_MODULE=config.settings.production

echo "==> Building CSS bundles"
python scripts/build_css_bundles.py

echo "==> Collecting static files (WhiteNoise)"
python manage.py collectstatic --noinput

echo "==> Applying database migrations (PostgreSQL)"
python manage.py migrate --noinput

echo "==> Django system checks"
python manage.py check --deploy || python manage.py check

echo "==> Build complete"
