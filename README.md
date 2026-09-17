# ECO CONTROL

Migração do protótipo ECO CONTROL para uma arquitetura local baseada em **Angular + FastAPI + PostgreSQL**.

## Stack

- **Frontend:** Angular 18 + TypeScript
- **Backend:** FastAPI + SQLAlchemy
- **Banco de dados:** PostgreSQL 16
- **Migrations:** Alembic
- **Banco local:** Docker Compose

---

## Pré-requisitos

Antes de executar o projeto, instale:

- Git
- Node.js 20+
- npm
- Python 3.11+
- Docker Desktop

---

## 1. Clonar o projeto

```bash
git clone https://github.com/KarolVSDev/eco-control.git
cd eco-control
```

---

## 2. Subir o PostgreSQL

Na raiz do projeto:

```bash
docker compose up -d db
```

Verifique o status:

```bash
docker compose ps
```

O serviço do PostgreSQL deve aparecer como `healthy`.

### Configuração local do banco

- **Host:** `localhost`
- **Porta:** `5432`
- **Banco:** `eco_control`
- **Usuário:** `eco_user`
- **Senha:** `eco_pass`

> Essas credenciais são destinadas somente ao ambiente local de desenvolvimento.

---

## 3. Configurar o Backend

Entre na pasta do backend:

```bash
cd server
```

Crie o ambiente virtual:

```bash
python -m venv .venv
```

### Windows PowerShell

```powershell
.\.venv\Scripts\Activate.ps1
```

### Linux/macOS

```bash
source .venv/bin/activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

Crie o arquivo `.env` a partir do exemplo.

### Windows PowerShell

```powershell
Copy-Item .env.example .env
```

### Linux/macOS

```bash
cp .env.example .env
```

Aplique as migrations:

```bash
alembic upgrade head
```

Execute o seed inicial:

```bash
python -m app.seed
```

O seed cria:

- usuário administrador local;
- mapeamentos OBU → AU;
- mapeamentos Owner → Group;
- dados sintéticos de ECO para desenvolvimento.

Execute a API:

```bash
uvicorn main:app --reload --port 8000
```

### Endereços do Backend

- **API:** http://localhost:8000
- **Swagger:** http://localhost:8000/docs
- **Health check:** http://localhost:8000/health

---

## 4. Configurar o Frontend

Abra outro terminal e entre na pasta do frontend:

```bash
cd client
```

Instale as dependências:

```bash
npm install
```

Execute o Angular:

```bash
npm start
```

### Endereço do Frontend

- http://localhost:4200

O frontend está configurado para consumir a API em:

```text
http://localhost:8000/api/v1
```

---

## Login de desenvolvimento

Depois de executar:

```bash
python -m app.seed
```

use:

- **E-mail:** `admin@eco.com`
- **Senha:** `admin123`

> Os dados gerados pelo seed são sintéticos e não contêm dados sensíveis da planilha original.

---

## Execução diária

Depois que o projeto já estiver configurado pela primeira vez, normalmente são necessários três terminais.

### Terminal 1 — PostgreSQL

Na raiz do projeto:

```bash
docker compose up -d db
```

### Terminal 2 — FastAPI

```powershell
cd server
.\.venv\Scripts\Activate.ps1
uvicorn main:app --reload --port 8000
```

### Terminal 3 — Angular

```bash
cd client
npm start
```

---

## Parar o banco

Para parar os containers sem apagar os dados:

```bash
docker compose down
```

Os dados permanecem no volume Docker.

Para apagar também os dados locais do PostgreSQL:

```bash
docker compose down -v
```

> Use `-v` somente quando realmente quiser recriar o banco do zero.

---

## Estrutura do projeto

```text
eco-control/
├── client/
│   ├── src/
│   ├── angular.json
│   ├── package.json
│   └── package-lock.json
│
├── server/
│   ├── alembic/
│   │   └── versions/
│   ├── app/
│   │   ├── config/
│   │   ├── controller/
│   │   ├── models/
│   │   ├── repository/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── utils/
│   │   └── seed.py
│   ├── tests/
│   ├── .env.example
│   ├── alembic.ini
│   ├── main.py
│   └── requirements.txt
│
├── docs/
├── docker-compose.yml
├── .gitignore
└── README.md
```

---

## Arquitetura

O fluxo principal da aplicação é:

```text
Angular
   ↓ HTTP / JSON
FastAPI
   ↓ SQLAlchemy
PostgreSQL
```

O frontend não acessa o PostgreSQL diretamente.

As regras de negócio, autenticação, autorização, persistência e auditoria devem ser validadas no backend.

---

## Teste de instalação em uma máquina nova

Uma instalação limpa deve funcionar nesta ordem:

```text
git clone
↓
docker compose up -d db
↓
python -m venv .venv
↓
ativar .venv
↓
pip install -r requirements.txt
↓
copiar .env.example para .env
↓
alembic upgrade head
↓
python -m app.seed
↓
uvicorn main:app --reload --port 8000
↓
npm install
↓
npm start
```

Depois valide:

1. `docker compose ps` mostra o PostgreSQL como `healthy`.
2. http://localhost:8000/health responde `{"status":"ok"}`.
3. http://localhost:8000/docs abre o Swagger.
4. http://localhost:4200 abre o Angular.
5. O login `admin@eco.com / admin123` funciona.

---

## Desenvolvimento em equipe

A separação principal do projeto é:

### Frontend

Responsável principalmente por:

```text
client/
```

Inclui:

- telas;
- componentes;
- formulários;
- tabelas;
- filtros;
- responsividade;
- integração com a API;
- aplicação visual das permissões.

### Backend

Responsável principalmente por:

```text
server/
```

Inclui:

- endpoints FastAPI;
- autenticação;
- permissões;
- regras de negócio;
- cálculos de ECO;
- SQLAlchemy;
- PostgreSQL;
- migrations;
- auditoria;
- testes.

### Documentação

Responsável principalmente por:

```text
README.md
docs/
```

Inclui:

- instalação;
- arquitetura;
- documentação dos endpoints;
- modelo de dados;
- decisões técnicas;
- fluxo de autenticação;
- permissões;
- guia para novos desenvolvedores.

---

## Arquivos que não devem ser versionados

O `.gitignore` do projeto exclui arquivos locais como:

- `client/node_modules/`
- `client/dist/`
- `client/.angular/`
- `server/.venv/`
- `server/__pycache__/`
- arquivos `.env`
- caches Python
- configurações locais de IDE

Nunca versione:

- senhas reais;
- tokens;
- chaves privadas;
- arquivos `.env`;
- dados sensíveis;
- planilhas reais de produção.

---

## Repositório

```text
https://github.com/KarolVSDev/eco-control
```
