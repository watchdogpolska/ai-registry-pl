# Development commands. Everything runs inside Docker Compose containers;
# no local Python, pip, Node or yarn is needed (or allowed).
#
#   make help        list targets
#   make test T=home.tests.PublicViewsSmokeTests
#   make manage ARGS="showmigrations home"

COMPOSE ?= docker compose
RUN     := $(COMPOSE) run --rm
DJANGO  := $(RUN) django
MANAGE  := $(DJANGO) python manage.py

# Tests need a DB user that can create test_* databases; the dev `ai_registry`
# user cannot, so tests use the (dev-only) MySQL root account.
MYSQL_ROOT_PASSWORD := changeme-root
ROOT_DB_URL := mysql://root:$(MYSQL_ROOT_PASSWORD)@mysql:3306
TEST_ENV := -e DJANGO_SETTINGS_MODULE=ai_registry.settings.test \
            -e DJANGO_HOME_PAGE_CACHE_SECONDS=0 \
            -e DATABASE_URL=$(ROOT_DB_URL)/ai_registry
# Throwaway database used by `make ci` to validate the snapshot, so the dev DB
# is never touched.
CI_DB := ai_registry_ci
# CI runs isort from the repo root, where `home` is not a first-party package;
# point --src elsewhere so the container (cwd /app) sorts imports the same way.
ISORT_ARGS := --profile black --src /nonexistent

T    ?=
ARGS ?=

.DEFAULT_GOAL := help
.PHONY: help build up start stop down restart logs ps \
        manage migrate makemigrations migrations-check createsuperuser \
        loaddata export shell bash dbshell \
        test format lint check css ci

help: ## Show this help
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# --- Stack -------------------------------------------------------------------

build: ## Build the development images
	$(COMPOSE) build

up: ## Start mysql + django + scss watcher in the foreground (http://localhost:8001/)
	$(COMPOSE) up --build

start: ## Start the stack in the background
	$(COMPOSE) up --build -d

stop: ## Stop the stack (keeps containers and data)
	$(COMPOSE) stop

down: ## Stop and remove containers (database volume is kept)
	$(COMPOSE) down

restart: ## Restart the django service
	$(COMPOSE) restart django

logs: ## Follow logs of all services
	$(COMPOSE) logs -f

ps: ## Show running services
	$(COMPOSE) ps

# --- Django ------------------------------------------------------------------

manage: ## Run any manage.py command: make manage ARGS="..."
	$(MANAGE) $(ARGS)

migrate: ## Apply migrations
	$(MANAGE) migrate

makemigrations: ## Create migrations for model changes
	$(MANAGE) makemigrations $(ARGS)

migrations-check: ## Fail if model changes are missing a migration
	$(MANAGE) makemigrations --check --dry-run

createsuperuser: ## Create an admin user
	$(MANAGE) createsuperuser

loaddata: ## Load data/registry.json (fresh/empty DB only!)
	$(MANAGE) loaddata data/registry.json

export: ## Refresh the data/registry.json snapshot from the dev DB
	$(MANAGE) export_registry_data

shell: ## Django shell (IPython)
	$(MANAGE) shell

bash: ## Bash inside the django container
	$(DJANGO) bash

dbshell: ## MySQL client connected to the dev database
	$(COMPOSE) exec mysql mysql -uai_registry -pchangeme ai_registry

# --- Quality -----------------------------------------------------------------

test: ## Run tests (optionally T=home.test_char32_uuid)
	$(RUN) $(TEST_ENV) django python manage.py test $(T)

format: ## Format code with black + isort
	$(DJANGO) sh -c "black . && isort . $(ISORT_ARGS)"

lint: ## Check formatting like CI (black + isort)
	$(DJANGO) sh -c "black . --check --diff && isort . --check --diff $(ISORT_ARGS)"

check: ## Django system checks
	$(MANAGE) check

# --- Frontend ----------------------------------------------------------------

css: ## Compile SCSS once into home/static/home/css/bundle.css
	$(RUN) scss-compile yarn build

# --- CI mirror ---------------------------------------------------------------

ci: lint migrations-check check ## Run the CI checks locally (lint, migrations, snapshot, tests)
	$(COMPOSE) up -d --wait mysql
	$(COMPOSE) exec mysql mysql -uroot -p$(MYSQL_ROOT_PASSWORD) -e \
		"DROP DATABASE IF EXISTS $(CI_DB); CREATE DATABASE $(CI_DB) CHARACTER SET utf8mb4 COLLATE utf8mb4_polish_ci;"
	$(RUN) $(TEST_ENV) -e DATABASE_URL=$(ROOT_DB_URL)/$(CI_DB) django \
		sh -c "python manage.py migrate --noinput && python manage.py loaddata data/registry.json"
	$(COMPOSE) exec mysql mysql -uroot -p$(MYSQL_ROOT_PASSWORD) -e "DROP DATABASE $(CI_DB);"
	$(MAKE) test
