.PHONY: test alembic_migrate

include .env

test:
	# Run tests using simulated github actions environment
	act

alembic_migrate:
	alembic upgrade head
