# Technology Stack

## Backend
- **Language:** Python 3.12+
- **Agent Framework:** Google ADK (Agent Development Kit)
- **API Framework:** FastAPI
- **Dependencies:** `google-adk`, `a2ui-agent-sdk`, `python-dotenv`, `google-api-python-client`, `google-auth`

## Frontend
- **Framework:** React
- **Build Tool:** Vite
- **Package Manager:** npm

## Database & Storage
- **Primary Database:** Google Sheets (managed via `gspread` or Google Sheets API)
- **Configuration:** Service Account (JSON) for authentication

## Infrastructure & DevOps
- **Containerization:** Docker
- **CI/CD:** Google Cloud Build
- **Local Dev Tool:** `uv` (Python package manager)
- **Quality Assurance:** Ruff (linting/formatting), Pytest (testing)