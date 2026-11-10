# ECO CONTROL

Aplicação web para gerenciamento e acompanhamento de ECOs (Engineering Change Orders), desenvolvida com Angular, FastAPI e PostgreSQL.

## Stack

- **Frontend:** Angular 18 + TypeScript
- **Backend:** FastAPI + SQLAlchemy
- **Banco de dados:** PostgreSQL 16
- **Migrations:** Alembic
- **Servidor web:** Nginx
- **Containerização:** Docker + Docker Compose

## Arquitetura

```text
Usuário
   ↓
Angular + Nginx
   ↓ /api/v1
FastAPI
   ↓
SQLAlchemy
   ↓
PostgreSQL
```

O frontend não acessa diretamente o banco de dados.

As regras de negócio, autenticação, autorização, auditoria e persistência são tratadas pelo backend.

---

## Pré-requisitos

Para executar a aplicação de forma containerizada, é necessário:

- Git
- Docker Desktop / Docker Engine
- Docker Compose

Node.js e Python não são necessários na máquina de deploy quando a aplicação é executada totalmente via Docker.

---

## Clonar o projeto

```bash
git clone https://github.com/KarolVSDev/eco-control.git
cd eco-control
```

---

## Configuração do ambiente

Copie o arquivo de exemplo:

### Windows PowerShell

```powershell
Copy-Item .env.example .env
```

### Linux

```bash
cp .env.example .env
```

Antes de utilizar em produção, configure no `.env` valores seguros para:

```env
POSTGRES_DB=eco_control
POSTGRES_USER=eco_user
POSTGRES_PASSWORD=senha-segura

JWT_SECRET=segredo-jwt-forte-e-aleatorio
ACCESS_TOKEN_MINUTES=480

CORS_ORIGINS=http://endereco-do-servidor

# Primeiro administrador (preencha com credenciais próprias)
ADMIN_EMAIL=
ADMIN_PASSWORD=
ADMIN_NAME=Administrador
```

O arquivo `.env` não deve ser versionado.

---

# Execução com Docker

Na raiz do projeto:

```bash
docker compose up -d --build
```

Esse comando inicializa:

- PostgreSQL;
- backend FastAPI;
- frontend Angular/Nginx.

Também são executadas automaticamente as migrations do Alembic antes da inicialização da API.

Verifique os containers:

```bash
docker compose ps
```

O resultado esperado é:

```text
eco-control-db          healthy
eco-control-backend     healthy
eco-control-frontend    running
```

---

## Endereços padrão

### Frontend

```text
http://localhost:4200
```

### Backend

```text
http://localhost:8001
```

### Swagger

```text
http://localhost:8001/docs
```

### Health check

```text
http://localhost:8001/health
```

### PostgreSQL

```text
Host: localhost
Porta: 5433
Banco: eco_control
```

---

# Instalação oficial

Uma instalação nova **não carrega ECOs fictícias automaticamente**.

Ao executar:

```bash
docker compose up -d --build
```

o sistema:

1. cria o PostgreSQL;
2. executa as migrations até a revisão mais recente;
3. cria a estrutura das tabelas;
4. inicia o backend;
5. inicia o frontend.

As ECOs permanecem vazias até que dados oficiais sejam inseridos pela aplicação ou pelas integrações autorizadas.

Para verificar a migration aplicada:

```bash
docker compose exec backend alembic current
```

Resultado esperado atualmente:

```text
0008 (head)
```

Para verificar a quantidade de ECOs:

```bash
docker compose exec db psql -U eco_user -d eco_control -c "SELECT COUNT(*) AS ecos FROM ecos;"
```

Em uma instalação nova:

```text
ecos
----
0
```

---

# Primeiro administrador

Defina `ADMIN_EMAIL`, `ADMIN_PASSWORD` e, opcionalmente, `ADMIN_NAME` no arquivo `.env` antes de iniciar os serviços. Ao executar `docker compose up -d --build`, depois das migrations, o backend cria automaticamente o primeiro administrador.

Se email ou senha não estiverem configurados, o bootstrap não executa. Se o usuário já existir, nenhum usuário será criado e sua senha e demais dados não serão alterados. O bootstrap é executado em cada startup e permanece idempotente.

Depois disso, os demais usuários podem ser administrados pela própria aplicação.

---

# Dados padrão

As migrations podem cadastrar configurações necessárias ao funcionamento da aplicação.

Atualmente:

- migration `0007`: mapeamentos padrão OBU → AU;
- migration `0008`: mapeamentos padrão Owner → Group.

Esses registros são independentes das ECOs e fazem parte da configuração inicial do sistema.

---

# Seed de demonstração

O módulo:

```bash
python -m app.seed
```

é destinado **exclusivamente a desenvolvimento e demonstração**.

Ele pode criar:

- administrador de demonstração;
- mapeamentos fictícios;
- ECOs sintéticas.

## Não execute `app.seed` no ambiente oficial.

Dados de demonstração não são executados automaticamente pelo `docker-compose.yml`.

---

# Parar a aplicação

Para parar os containers preservando o banco:

```bash
docker compose down
```

Os dados continuam armazenados no volume Docker.

Para iniciar novamente:

```bash
docker compose up -d
```

---

# Atenção ao volume do PostgreSQL

O comando:

```bash
docker compose down -v
```

remove também o volume do PostgreSQL.

Isso significa que os dados armazenados no banco serão apagados.

**Não execute `docker compose down -v` no ambiente oficial, salvo quando houver intenção explícita de excluir e recriar o banco.**

---

# Logs

Backend:

```bash
docker compose logs backend --tail 100
```

Frontend:

```bash
docker compose logs frontend --tail 100
```

Banco:

```bash
docker compose logs db --tail 100
```

Acompanhar logs em tempo real:

```bash
docker compose logs -f
```

---

# Estrutura principal

```text
eco-control/
├── client/
│   ├── src/
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── angular.json
│   └── package.json
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
│   │   ├── bootstrap_admin.py
│   │   └── seed.py
│   ├── tests/
│   ├── Dockerfile
│   ├── alembic.ini
│   ├── main.py
│   └── requirements.txt
│
├── docs/
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

# Desenvolvimento local sem Docker completo

Para desenvolvimento, os serviços também podem ser executados separadamente.

### Banco

```bash
docker compose up -d db
```

### Backend

```powershell
cd server
.\.venv\Scripts\Activate.ps1
alembic upgrade head
uvicorn main:app --reload --port 8001
```

### Frontend

```bash
cd client
npm install
npm start
```

O ambiente manual é destinado principalmente ao desenvolvimento.

Para deploy e homologação, prefira o fluxo completo com:

```bash
docker compose up -d --build
```

---

# Segurança

Nunca versione:

- arquivos `.env`;
- senhas reais;
- tokens;
- JWT secrets;
- chaves privadas;
- planilhas oficiais com dados sensíveis;
- dumps de banco de produção.

Credenciais e segredos do ambiente oficial devem ser definidos somente no servidor de deploy.

---

# Repositório

```text
https://github.com/KarolVSDev/eco-control
```