# Deployment notes — Cementne košuljice Ivkov

## Stack

| Component | Local | Production |
|-----------|-------|------------|
| Python | 3.13.5 | 3.13.5 |
| Django | 5.2.x | 5.2.x |
| Database | SQLite (`db.sqlite3`) | PostgreSQL (`DATABASE_URL`) |
| Static files | WhiteNoise | WhiteNoise |
| WSGI server | `runserver` | Gunicorn |

Settings module is selected **only** via `DJANGO_SETTINGS_MODULE` — no code changes between environments.

---

## Local development

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
- Contact: http://localhost:8000/kontakt/

---

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DJANGO_SETTINGS_MODULE` | Yes | `config.settings.local` or `config.settings.production` |
| `SECRET_KEY` | Yes | Django secret key |
| `DEBUG` | Yes | `True` locally, `False` in production |
| `ALLOWED_HOSTS` | Yes | Comma-separated hostnames |
| `DATABASE_URL` | Production | PostgreSQL URL (set automatically on Render) |
| `SITE_BASE_URL` | Recommended | Full public URL, e.g. `https://your-app.onrender.com` |
| `CONTACT_PHONE` | Recommended | Public phone number |
| `USE_R2_STORAGE` | Production | `True` for Cloudflare R2 (default in production) |
| `AWS_*` | Production | R2 API credentials and bucket (see Media storage) |
| `MEDIA_URL` | Production | Public base URL for uploaded files |

See `.env.example` for a full local template.

---

## Render.com deployment

### Blueprint (`render.yaml`)

1. Push the repository to GitHub/GitLab
2. In Render: **New → Blueprint** → connect repo
3. Set sync=false variables in the dashboard:
   - `SITE_BASE_URL` → `https://<your-service>.onrender.com`
   - R2 credentials (`AWS_*`, `MEDIA_URL`)

### Post-deploy

```bash
python manage.py createsuperuser
```

---

## Media storage (Cloudflare R2)

Production uses **Cloudflare R2** via `django-storages` + `boto3` (`config/storages.py`).

| Storage alias | Path in bucket | Purpose |
|---------------|----------------|---------|
| `blog_images` | `blog/images/` | Blog and builder image uploads |
| `project_videos` | `projects/videos/` | Builder video files |

**R2 environment variables** (preferred):

| Variable | Purpose |
|----------|---------|
| `R2_ACCESS_KEY_ID` | R2 API access key |
| `R2_SECRET_ACCESS_KEY` | R2 API secret |
| `R2_BUCKET_NAME` | Bucket name |
| `R2_ENDPOINT_URL` | `https://<ACCOUNT_ID>.r2.cloudflarestorage.com` |
| `R2_REGION_NAME` | `auto` (optional) |
| `R2_CUSTOM_DOMAIN` | e.g. `media.cementne-kosuljice.rs` |
| `R2_MEDIA_URL` | e.g. `https://media.cementne-kosuljice.rs/` |

Legacy `AWS_*` names are still accepted as fallbacks.

**R2 setup:**

1. Cloudflare Dashboard → R2 → Create bucket
2. Manage R2 API tokens → Create token (Object Read & Write)
3. Optional: connect custom domain (e.g. `media.yourdomain.com`)
4. Set on Render:

```
USE_R2_STORAGE=True
R2_ACCESS_KEY_ID=<R2 access key>
R2_SECRET_ACCESS_KEY=<R2 secret>
R2_BUCKET_NAME=your-bucket
R2_ENDPOINT_URL=https://<ACCOUNT_ID>.r2.cloudflarestorage.com
R2_REGION_NAME=auto
R2_CUSTOM_DOMAIN=media.yourdomain.com
R2_MEDIA_URL=https://media.yourdomain.com/
```

Local development uses `MEDIA_ROOT` (`media/` folder) — no R2 credentials required.

There is **automatic media deletion** when database records are removed or media fields are replaced — see `apps/core/media_signals.py`. Orphaned files can be cleaned with `python manage.py cleanup_orphaned_media` or `python manage.py audit_orphaned_data --fix`.

---

## Localization

- `LANGUAGE_CODE = sr-latn` (Serbian Latin only)
- `TIME_ZONE = Europe/Belgrade`

---

## Environment switching

| Environment | `DJANGO_SETTINGS_MODULE` | Database | Media |
|-------------|--------------------------|----------|-------|
| Local | `config.settings.local` | SQLite | `MEDIA_ROOT` |
| Production | `config.settings.production` | PostgreSQL | Cloudflare R2 |

Verify both settings modules:

```bash
python scripts/verify_environments.py
```

---

## Static files

| Layer | Mechanism | Cache |
|-------|-----------|-------|
| Build | `collectstatic` → `staticfiles/` | — |
| Serve | WhiteNoise | 1 year |
| URL | `/static/` | Fingerprinted filenames |

After CSS edits run `python scripts/build_css_bundles.py` then redeploy.

---

## Security (production)

Configured in `config/settings/production.py` and `apps/core/middleware.py`:

| Control | Implementation |
|---------|----------------|
| HSTS | `SECURE_HSTS_SECONDS`, include subdomains, preload |
| CSP | `Content-Security-Policy` on public pages |
| Secure cookies | `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` |
| CSRF | `CSRF_TRUSTED_ORIGINS` from hosts / `SITE_BASE_URL` |
| HTTPS | `SECURE_SSL_REDIRECT`, `SECURE_PROXY_SSL_HEADER` |

Full checklist: **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)**
