.PHONY: install
install:
	uv sync

.PHONY: clean
clean:
	rm -rf dist/
	find . -name '__pycache__' -exec rm -fr {} +

.PHONY: typecheck
typecheck:
	uv run pyright

.PHONY: lint
lint:
	-uv run ruff check --fix
	-uv run ruff format

.PHONY: lint_unsafe
lint_unsafe:
	-uv run ruff check --fix --unsafe-fixes
	-uv run ruff format

.PHONY: lint_no_fix
lint_no_fix:
	uv run ruff check
	uv run ruff format --check

.PHONY: test
test:
	uv run pytest
