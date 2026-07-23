.PHONY: install sample run test lint typecheck check clean

install:          ## Instala el paquete en modo editable con extras de desarrollo
	python -m pip install -e ".[dev]"

sample:           ## Genera el dataset de muestra con defectos inyectados
	python scripts/generate_sample_data.py data/reviews_sample.csv

run: sample       ## Ejecuta el análisis sobre el dataset de muestra
	python -m flowapp_reviews data/reviews_sample.csv

test:             ## Corre la suite de pruebas con reporte de cobertura
	pytest --cov --cov-report=term-missing

lint:             ## Verifica estilo y errores estáticos
	ruff check src tests scripts

typecheck:        ## Verifica tipos en modo estricto
	mypy

check: lint typecheck test  ## Todo lo anterior

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov build dist
	find . -name "__pycache__" -type d -exec rm -rf {} +
