# ECO CONTROL — Angular + FastAPI + PostgreSQL

Refatoração local do protótipo ECO CONTROL exportado do Base44.

## Stack
- Angular 18 + TypeScript
- FastAPI + SQLAlchemy + Alembic
- PostgreSQL 16
- Docker Compose para banco local

## Pré-requisitos
- Node.js 20+
- Python 3.11+
- Docker Desktop (recomendado para PostgreSQL)

## 1. Banco de dados
```bash
docker compose up -d db
```

## 2. Backend
```bash
cd server
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
# source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env   # Windows
# cp .env.example .env   # Linux/macOS
alembic upgrade head
python -m app.seed
uvicorn main:app --reload --port 8000
```

API: http://localhost:8000  
Swagger: http://localhost:8000/docs

## 3. Frontend
```bash
cd client
npm install
npm start
```

Frontend: http://localhost:4200

## Login de desenvolvimento
- E-mail: `admin@eco.local`
- Senha: `admin123`

> Os dados de seed são sintéticos e não contêm informações da planilha sensível original.

## Estrutura
- `client/`: Angular modularizado por feature
- `server/`: FastAPI em Controller → Service → Repository
- `docs/`: mapa de migração e decisões técnicas
