.PHONY: dev lint test check

dev:
	docker-compose up -d redis
	uv run uvicorn app.main:app --reload --port 8123 &
	cd frontend && npm run dev

lint:
	uv run ruff check app/ tests/
	uv run ruff format --check app/ tests/
	cd frontend && npm run lint

test:
	uv run python -m pytest tests/ -v
	cd frontend && npx vitest run

check: lint test
