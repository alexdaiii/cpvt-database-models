.PHONY: test alembic_migrate

include .env

test:
	# Run tests using simulated github actions environment
	poetry run pytest --junitxml=report.xml --color=yes --cov=cpvt_database_models --cov-append --cov-report=term-missing -n auto
	coverage html

alembic_migrate:
	alembic upgrade head
