.PHONY: install web cli server server-prod ui ui-prod ui-install lint format test test-ui check env auth help

help:
	@echo "Comandos disponibles:"
	@echo "  make install    Instala dependencias con uv"
	@echo "  make web        Lanza Luppita en interfaz web ADK (localhost:8000)"
	@echo "  make server     Lanza API server ADK (localhost:8001) para el chat web"
	@echo "  make server-prod Lanza el servidor FastAPI igual que Cloud Run (localhost:8080)"
	@echo "  make ui-install Instala dependencias del frontend React"
	@echo "  make ui         Lanza el frontend React (localhost:5173)"
	@echo "  make cli        Lanza Luppita en línea de comandos"
	@echo "  make lint       Verifica el código con ruff"
	@echo "  make format     Formatea el código con ruff"
	@echo "  make test       Corre los tests con pytest"
	@echo "  make test-ui    Corre los tests de UI con Playwright/Gherkin"
	@echo "  make check      Verifica que las herramientas y Sheets cargan"
	@echo "  make env        Crea .env desde .env.example"
	@echo "  make auth       Crea Service Account y descarga clave para Sheets"

install:
	uv sync

web:
	uv run adk web

server:
	A2UI_ENABLED=true uv run adk api_server --port 8001 --allow_origins "http://localhost:5173" .

server-prod:
	A2UI_ENABLED=true ALLOW_ORIGINS=http://localhost:5173 uv run uvicorn app.fast_api_app:app --host 0.0.0.0 --port 8080 --reload

ui-install:
	cd web && npm install

ui:
	cd web && npm run dev

# Override with: make ui-prod VITE_API_URL=https://your-cloud-run-url
ui-prod:
	cd web && VITE_API_URL=$(VITE_API_URL) npm run dev

cli:
	uv run adk run luppita

lint:
	uv run ruff check .

format:
	uv run ruff format .

test:
	uv run pytest

check:
	uv run python -c "from luppita.tools import ALL_TOOLS; print(f'{len(ALL_TOOLS)} herramientas cargadas')"
	uv run python -c "from luppita.sheets import read_sheet; rows = read_sheet('Config'); print(f'Sheets OK: {len(rows)} filas en Config')"

env:
	cp .env.example .env
	@echo "Archivo .env creado. Edítalo con tus valores."

# Override with: make auth GCP_PROJECT=your-project-id
GCP_PROJECT ?= $(shell grep GOOGLE_CLOUD_PROJECT .env 2>/dev/null | cut -d= -f2)
SA_NAME     ?= luppita-agent
SA_EMAIL    ?= $(SA_NAME)@$(GCP_PROJECT).iam.gserviceaccount.com

auth:
	mkdir -p credentials
	gcloud iam service-accounts create $(SA_NAME) --display-name="Luppita Agent" --project=$(GCP_PROJECT) 2>/dev/null || true
	gcloud iam service-accounts keys create credentials/luppita-sa.json \
		--iam-account=$(SA_EMAIL)
	@echo ""
	@echo "SA creada. Comparte el sheet con: $(SA_EMAIL) (Editor)"

test-ui:
	cd web && npm run test:ui
