.PHONY: coverage

coverage:
	pytest --cov=cpvt_website_models tests/ -n auto
	coverage html


alembic_migrate:
	alembic upgrade head
