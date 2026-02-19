.PHONY: install run test clean format lint

install:
	python -m venv venv
	. venv/bin/activate && pip install -r requirements.txt

run:
	streamlit run app/streamlit_app.py

test:
	pytest tests/ -v

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +

format:
	black .

lint:
	mypy models/ agents/ app/ utils/

help:
	@echo "Available commands:"
	@echo "  make install  - Create venv and install dependencies"
	@echo "  make run      - Run the Streamlit application"
	@echo "  make test     - Run tests"
	@echo "  make clean    - Remove cache files"
	@echo "  make format   - Format code with black"
	@echo "  make lint     - Run type checking with mypy"