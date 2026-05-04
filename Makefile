install:
	pip install -r requirements.txt -r requirements-dev.txt

test:
	pytest tests/ -v

lint:
	flake8 src/ tests/

format:
	black src/ tests/

typecheck:
	mypy src/

ui:
	streamlit run app.py
