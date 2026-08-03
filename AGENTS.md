# AGENTS.md

Legacy Django 2.1 e-commerce app ("shop") with session-based cart, Celery/Redis, and SendGrid email. Deployed on AWS Elastic Beanstalk. Code comments and some UI text are in Traditional Chinese.

## Setup & commands

- Project pins 2020-era deps (`Django==2.1.1`, `djangorestframework==3.11.0`, `celery==4.4.0`, `mysqlclient==1.4.6`, `Pillow==7.0.0`) that need **Python 3.8** — do not upgrade.
- The global `python3` (3.8) has Django 4.2.8 installed but **no celery**, so running `manage.py` bare fails with `ModuleNotFoundError: No module named 'celery'`. Always use a venv:
  - `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt` (mysqlclient may need MySQL dev headers)
- Run server: `python manage.py runserver`
- Tests: `python manage.py test` — real tests in `products/tests/` (`test_models.py`, `test_views.py`), plus `orders/tests.py`, `api/tests.py`, `shop/tests.py` covering checkout atomicity, order authorization, the DRF API, and settings security.
- No lint, formatter, or typecheck config; no CI. Nothing to run besides tests.

## Docker Compose (local stack)

- Stack: `web` (Django dev server on `http://localhost:8000`), `worker` (Celery), `migrate` (one-shot, runs before web/worker), `mysql:5.7`, `redis:6`.
- Commands:
  - `docker compose up --build` — build, migrate, boot everything.
  - `docker compose ps` / `docker compose logs -f web` — inspect.
  - `docker compose down` — stop (keeps the `mysql_data` volume); `docker compose down -v` also wipes the DB.
- Env vars come from `env.yaml` at the repo root (gitignored; `cp env.example.yaml env.yaml` on a fresh clone). The container `entrypoint.sh` parses it with `scripts/yaml_to_env.py` (prints shell `export`s) and `exec`s the command — **not** Compose's `!include`/`env_file`, since this Compose build doesn't support `!include` for env and `env_file` is dotenv-only.
- `env.yaml` sets `RDS_HOSTNAME=mysql` etc., so the container always uses MySQL (never SQLite). Verify container env via `docker compose exec web cat /proc/1/environ` — `docker compose exec` spawns a fresh process that does NOT inherit entrypoint-exported vars.
- DB passwords for `mysql` come from the inline `MYSQL_*` vars in `docker-compose.yml` (root: `rootpass`, db/user/password `shop`); they must match `env.yaml`. MySQL port 3306 is not exposed to the host.
- `mysql:5.7` is used deliberately: the 2020-era `mysqlclient==1.4.6` builds against the MariaDB C client and can fail auth against MySQL 8's `caching_sha2_password`.
- The `python:3.8-slim-buster` base is EOL; the Dockerfile repoints apt to `archive.debian.org` so `pip install` (compiles `mysqlclient`, `gevent`, `greenlet`, `Pillow`) succeeds. Build takes ~3 min.
- To run a Django management command with the stack's env (e.g. `createsuperuser`), wrap it in the entrypoint: `docker compose exec web /app/entrypoint.sh python manage.py createsuperuser`.

## Architecture

- Project package `shop` (`shop/settings.py`, `shop/urls.py`); apps: `products`, `users`, `cart`, `orders`, `api`. URLs mounted at `/product/`, `/user/`, `/cart/`, `/order/`, `/api/`, `/admin/`; media served at `/media/`.
- Cart is session-based (`CART_SESSION_ID='cart'`) — see `cart/cart.py`; the web UI cart lives in `/cart/`, while the DRF app `api` (`/api/`) has its own read-only GET endpoints.
- `orders/views.py` calls the Celery task `send_order_success_email(...)` via `.delay()` inside a `try/except` that logs failures, so checkout still works without a Redis worker (the email just may not be sent).

## Env-var-driven config (all optional locally)

- DB: if `RDS_HOSTNAME` is set → MySQL via `RDS_*` env vars (Elastic Beanstalk); otherwise SQLite `db.sqlite3` (gitignored, not committed). Tests use an in-memory SQLite test DB.
- Celery + Django cache: `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` (Redis). When `CELERY_BROKER_URL` is set, the cache uses `django_redis` at that URL; otherwise it falls back to `LocMemCache` (so no Redis is needed locally).
- Email: `EMAIL_BACKEND = "sendgrid_backend.SendgridBackend"`, requires `SENDGRID_API_KEY`. Without it, checkout and password-reset emails raise.

## Deploy

- AWS Elastic Beanstalk via `.ebextensions/`: `WSGIPath: shop/wsgi.py`, container command runs `django-admin.py migrate` (leader only), Redis ElastiCache (`cache.t2.micro`), MySQL from `RDS_*` env vars.
- `SECRET_KEY` and `DEBUG` come from env vars (`SECRET_KEY`, `DJANGO_DEBUG`); defaults are a dev-only placeholder key and `DEBUG=False`. `ALLOWED_HOSTS` still lists the EB hostname and a public IP — set `DJANGO_DEBUG=True` for local dev.

## Quirks / gotchas

- `Product.save()` sets the slug on create only (`unidecode` + `allow_unicode`, unique suffix on collision) and resizes an uploaded image to 300x300 (`IOError`/`OSError` swallowed) — see `products/models.py`.
- `Product.image` default is `'/default.jpg'`; `media/` is gitignored (not committed), so a fresh checkout has no `default.jpg` and no uploads until you add them. `STATICFILES_DIRS` includes `media/` alongside `STATIC_ROOT=static/`, so `collectstatic` also copies media files.
- The original products/orders migrations are a chain of `AlterField`s that, on a fresh SQLite DB, trigger Django 2.1.1's table-remake bug and produce FKs pointing at dropped `*__old` tables (breaks INSERTs). `products/migrations/0001_initial_squashed_0008_*.py` and `orders/migrations/0001_initial_squashed_0004_*.py` (generated by `squashmigrations`, with the `AddField` inlined into `CreateModel`) are required for SQLite/tests to work. Do not regress the original migrations without it.
- `shop/__init__.py` deliberately does NOT import the WSGI app — importing it makes `manage.py` fail with `RuntimeError: populate() isn't reentrant`.
- `TIME_ZONE = 'Asia/Taipei'`; some templates/tests print Chinese text — don't "fix" it as a typo.
