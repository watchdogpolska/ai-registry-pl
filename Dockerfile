# syntax=docker/dockerfile:1

# Frontend assets -------------------------------------------------------------
FROM node:24-alpine AS scss-base
WORKDIR /build

COPY scss-compile/package.json scss-compile/yarn.lock ./
RUN yarn install --frozen-lockfile

COPY scss-compile/.browserslistrc ./
COPY scss-compile/scss ./scss

FROM scss-base AS scss-development
CMD ["yarn", "dev"]

FROM scss-base AS scss-build
RUN yarn build


# Python dependencies ---------------------------------------------------------
FROM python:3.14-slim-trixie AS python-base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update --yes --quiet \
    && apt-get install --yes --quiet --no-install-recommends \
        build-essential \
        default-libmysqlclient-dev \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements /requirements


# Development image -----------------------------------------------------------
FROM python-base AS development

RUN pip install --no-cache-dir -r /requirements/dev.txt
RUN useradd --create-home django

COPY --chown=django:django ai_registry/ /app/

USER django
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]


# Production dependency builder ----------------------------------------------
FROM python-base AS production-builder

RUN python -m venv /venv \
    && /venv/bin/pip install --no-cache-dir --upgrade pip \
    && /venv/bin/pip install --no-cache-dir -r /requirements/production.txt


# Production image ------------------------------------------------------------
FROM python:3.14-slim-trixie AS production

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=ai_registry.settings.prod \
    PATH="/venv/bin:$PATH"

RUN apt-get update --yes --quiet \
    && apt-get install --yes --quiet --no-install-recommends libmariadb3 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home django

WORKDIR /app

COPY --from=production-builder /venv /venv
COPY ai_registry/ /app/
COPY --from=scss-build /build/static/css /app/home/static/home/css

# collectstatic does not access the database, but production settings
# intentionally require deployment secrets/configuration. Use build-only values.
RUN DJANGO_SECRET_KEY=build-only-not-for-runtime \
    DJANGO_ALLOWED_HOSTS=localhost \
    DJANGO_CSRF_TRUSTED_ORIGINS=https://localhost \
    DATABASE_URL=mysql://build:build@localhost/build \
    python manage.py collectstatic --noinput

RUN chown -R django:django /app

# Release metadata shown in the footer. Declared last so a new version does not
# invalidate the dependency and collectstatic layers.
ARG APP_VERSION=dev
ARG APP_COMMIT=
ENV APP_VERSION=$APP_VERSION \
    APP_COMMIT=$APP_COMMIT

USER django
EXPOSE 8000

CMD ["gunicorn", "ai_registry.wsgi:application", "--bind", "0.0.0.0:8000", "--access-logfile", "-", "--error-logfile", "-"]
