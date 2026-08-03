# Shop Everything

Legacy Django 2.1 e-commerce app with a session-based cart, Celery/Redis async email, and a DRF read-only API. The UI and code comments are in Traditional Chinese. Deployed on AWS Elastic Beanstalk.

## Features

- Product catalog with search and pagination
- Session-based shopping cart (`CART_SESSION_ID='cart'`)
- User auth: signup, login/logout, password change/reset
- Checkout with atomic order creation and stock validation
- Celery async order email via SendGrid (fails gracefully without a worker)
- Read-only REST API under `/api/`

## Tech stack

- Python 3.8, Django 2.1.1, Django REST Framework 3.11
- Celery 4.4 + Redis (broker/cache), MySQL or SQLite
- Bootstrap 4.4 front-end
- 2020-era pinned deps in `requirements.txt` — **do not upgrade**

## Prerequisites

- **Python 3.8** (required by the pinned deps; newer Pythons won't install them)
- Docker + Docker Compose v2 (for the containerized stack)
- MySQL dev headers if installing `mysqlclient` locally

## Local (venv) setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver   # http://localhost:8000
```

Without `RDS_HOSTNAME` set, the app uses SQLite (`db.sqlite3`). Tests use an in-memory SQLite DB.

## Docker Compose (recommended)

The stack runs `web` (Django dev server), `worker` (Celery), a `migrate` one-shot, `mysql:5.7`, and `redis:6`.

```bash
cp env.example.yaml env.yaml   # first time only; env.yaml is gitignored
docker compose up --build      # builds (~3 min), migrates, boots everything
```

- App: http://localhost:8000
- Inspect: `docker compose ps`, `docker compose logs -f web`
- Stop: `docker compose down` (keeps the `mysql_data` volume); `docker compose down -v` also wipes the DB

Environment variables come from `env.yaml` (loaded by the container `entrypoint.sh`). To run a management command with the stack's env, wrap it in the entrypoint:

```bash
docker compose exec web /app/entrypoint.sh python manage.py createsuperuser
```

If MySQL is left in the `latin1` charset, Chinese inserts fail with `OperationalError (1366)` — the compose file sets utf8mb4; run `docker compose down -v` after pulling a fresh clone.

## Environment variables

| Variable | Purpose | Default |
| --- | --- | --- |
| `RDS_HOSTNAME`, `RDS_DB_NAME`, `RDS_USERNAME`, `RDS_PASSWORD`, `RDS_PORT` | MySQL connection; unset → SQLite | — |
| `SECRET_KEY` | Django secret key | dev-only placeholder |
| `DJANGO_DEBUG` | `"True"` enables debug mode | `"False"` |
| `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` | Redis URLs; unset → no worker + LocMemCache | — |
| `DEFAULT_FROM_EMAIL` | Order email sender | `shopEveryThing@myshop.com` |
| `SENDGRID_API_KEY` | SendGrid API key (email backend) | — |

## Project structure

- `shop/` — settings, URLs, WSGI, Celery app
- `products/`, `users/`, `cart/`, `orders/`, `api/` — apps; URLs at `/product/`, `/user/`, `/cart/`, `/order/`, `/api/`, `/admin/`
- `templates/` — site templates; `products/static/` — app CSS
- `scripts/yaml_to_env.py` — loads `env.yaml` into the container environment

## Tests

```bash
python manage.py test
```

Real tests cover checkout atomicity, order authorization, the DRF API, settings security, cart semantics, signup/login, search, and pagination.

## Deployment

AWS Elastic Beanstalk via `.ebextensions/`: `WSGIPath: shop/wsgi.py`, leader-only `migrate`, Redis ElastiCache, and MySQL from `RDS_*` env vars. Set `SECRET_KEY` and `DJANGO_DEBUG` in the EB environment.
