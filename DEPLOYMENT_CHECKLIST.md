# Production deployment checklist

Use this list before and after deploying to **Render** with **Cloudflare** (DNS / R2 / optional proxy).

---

## Pre-deploy (repository)

- [ ] `DJANGO_SETTINGS_MODULE` is **not** hardcoded in code — only via environment
- [ ] `python scripts/verify_environments.py` passes (local + production settings)
- [ ] `pip install -r requirements.txt` succeeds on Python 3.13.5
- [ ] `SECRET_KEY` generated (never commit `.env`)
- [ ] `.env` and credentials are in `.gitignore`

---

## Render — web service

- [ ] Blueprint applied from `render.yaml` or service created manually
- [ ] **PostgreSQL** database linked (`DATABASE_URL` auto-set)
- [ ] `DJANGO_SETTINGS_MODULE=config.settings.production`
- [ ] `DEBUG=False`
- [ ] `ALLOWED_HOSTS` includes `your-app.onrender.com` and custom domain(s)
- [ ] `SITE_BASE_URL=https://your-public-url` (no trailing path)
- [ ] `SECURE_SSL_REDIRECT=True`
- [ ] Health check path: `/health/`
- [ ] Build command: `./build.sh`
- [ ] Start command: `gunicorn config.wsgi:application -c config/gunicorn.conf.py`

---

## Security

- [ ] Unique `SECRET_KEY` on Render (auto-generated is OK)
- [ ] **HSTS** enabled (`SECURE_HSTS_SECONDS`, subdomains, preload if on custom domain)
- [ ] **HTTPS** redirect via `SECURE_SSL_REDIRECT` + Render TLS
- [ ] **Secure cookies**: `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` (production)
- [ ] **CSRF**: `CsrfViewMiddleware` active; `CSRF_TRUSTED_ORIGINS` includes public URL(s)
- [ ] **CSP** applied on public pages (`Content-Security-Policy` header)
- [ ] Django `/admin/` protected with strong passwords

---

## Cloudflare R2 (media)

- [ ] R2 bucket created
- [ ] API token with Object Read & Write
- [ ] Render env: `USE_R2_STORAGE=True`, `AWS_*`, `MEDIA_URL`
- [ ] Public custom domain for media (recommended): `R2_CUSTOM_DOMAIN`, `R2_MEDIA_URL=https://media.example.com/`
- [ ] `CSP_EXTRA_MEDIA_ORIGINS` set if extra CDN host needed
- [ ] `REQUIRE_R2_CONFIG=True` when credentials are final

---

## Cloudflare DNS / proxy (optional)

- [ ] DNS points to Render (CNAME or A)
- [ ] SSL mode: **Full (strict)** when using Render HTTPS
- [ ] If orange-cloud proxy enabled: set `USE_CLOUDFLARE_PROXY=True` on Render
- [ ] Cache rules: bypass cache for `/admin/*`; cache static on R2 domain

---

## Post-deploy commands (Render shell)

```bash
python manage.py createsuperuser
```

- [ ] Smoke test: home (`/`), usluge, kontakt, projekti, blog

---

## PostgreSQL migrations

- [ ] `build.sh` runs `migrate` on each deploy
- [ ] Never edit applied migrations on production
- [ ] Backup database before risky migrations (Render dashboard / pg_dump)

---

## Static files

- [ ] `collectstatic` runs in `build.sh`
- [ ] WhiteNoise serves `/static/` from `staticfiles/`
- [ ] After CSS/JS changes: run `python scripts/build_css_bundles.py`, then redeploy

---

## Verification URLs

| Check | URL |
|-------|-----|
| Health | `https://<host>/health/` → `{"status":"ok"}` |
| Home | `/` |
| Admin | `/admin/` |
| Static | `/static/css/bundles/site-core.css` (200) |
