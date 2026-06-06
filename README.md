# Cementne košuljice Ivkov — Django sajt

Production-ready Django 5 project for **Cementne košuljice Ivkov**.

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

- Site: http://localhost:8000/
- Django admin: http://localhost:8000/admin/

See [DEPLOYMENT.md](DEPLOYMENT.md) for Render deployment and environment configuration.

## Project structure

```
apps/
  core/       # Branding, middleware, health check
  frontend/   # Public pages (home, usluge, kontakt, projekti, blog)
  seo/        # Meta tags, sitemap, robots.txt
  blog/       # Blog posts + page builder
  layout/     # Projekti CMS page + page builder models
config/
  settings/
  urls.py
templates/
static/
manage.py
requirements.txt
```
