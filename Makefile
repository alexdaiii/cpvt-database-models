.PHONY: test alembic_migrate

test:
	# Run tests
	tox run
	# generate coverage html report
	coverage html

alembic_migrate:
	alembic upgrade head
