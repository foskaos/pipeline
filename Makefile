
test:
	pytest .

run-pipeline:
	python manage.py run_pipeline

help:
	@echo "Available commands:"
	@echo "  make test     		   - Run tests using pytest"
	@echo "  make run-pipleine     - Runs pipeline"
