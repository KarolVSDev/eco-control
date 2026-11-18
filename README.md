# ECO CONTROL

Aplicação web para gerenciamento e acompanhamento de ECOs (Engineering Change Orders), desenvolvida com Angular, FastAPI e PostgreSQL.

## Stack

- **Frontend:** Angular 18 + TypeScript
- **Backend:** FastAPI + SQLAlchemy
- **Banco de dados:** PostgreSQL 16
- **Migrations:** Alembic
- **Servidor web:** Nginx
- **Containerização:** Docker + Docker Compose

---

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

# Pré-requisitos

Para executar a aplicação de forma containerizada, é necessário:

- Git
- Docker Desktop / Docker Engine
- Docker Compose

Node.js e Python não são necessários quando a aplicação é executada totalmente via Docker.

Para verificar se os requisitos estão instalados:

```bash
git --version
docker --version
docker compose version
```

---

# Executando em uma nova máquina

## 1. Clonar o projeto

```bash
git clone https://github.com/KarolVSDev/eco-control.git
cd eco-control
```

Caso seja necessário utilizar uma branch específica:

```bash
git fetch origin
git switch nome-da-branch
git pull origin nome-da-branch
```

---

## 2. Criar o arquivo de ambiente

O Docker Compose utiliza o arquivo `.env` localizado na raiz do projeto.

Crie o arquivo a partir do modelo `.env.example`.

### Windows PowerShell

```powershell
Copy-Item .env.example .env
```

### Linux

```bash
cp .env.example .env
```

O `.env` deve conter configurações semelhantes a:

```env
POSTGRES_DB=eco_control
POSTGRES_USER=eco_user
POSTGRES_PASSWORD=change-this-in-production

JWT_SECRET=change-this-to-a-long-random-secret
ACCESS_TOKEN_MINUTES=480

CORS_ORIGINS=http://localhost:4200

ADMIN_EMAIL=admin@eco.com
ADMIN_PASSWORD=ecos2026@
ADMIN_NAME=Administrador
```

O arquivo `.env` real **não deve ser enviado para o Git**.

---

# Configuração das chaves e senhas

Para execução local, os valores do `.env.example` podem ser utilizados conforme a necessidade do ambiente.

Para homologação ou ambiente oficial, substitua os valores de exemplo de:

```env
POSTGRES_PASSWORD=change-this-in-production
JWT_SECRET=change-this-to-a-long-random-secret
```

por valores fortes e aleatórios.

## O que são esses valores?

### POSTGRES_PASSWORD

É a senha utilizada pelo usuário do banco PostgreSQL.

O backend utiliza essa mesma senha para conseguir se conectar ao banco.

### JWT_SECRET

É uma chave secreta utilizada pelo backend para assinar e validar os tokens de autenticação dos usuários.

Essa chave não é uma senha digitada pelos usuários da aplicação.

---

# Gerando valores seguros

Os valores podem ser gerados diretamente na máquina onde a aplicação será executada.

## Linux

Gerar uma senha para o PostgreSQL:

```bash
openssl rand -hex 24
```

Gerar uma chave JWT:

```bash
openssl rand -hex 32
```

Execute os comandos separadamente e coloque os valores gerados no `.env`.

Exemplo:

```env
POSTGRES_PASSWORD=<valor-gerado>
JWT_SECRET=<outro-valor-gerado>
```

---

## Windows PowerShell

Gerar `POSTGRES_PASSWORD`:

```powershell
$bytes = New-Object byte[] 24
[System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
($bytes | ForEach-Object { $_.ToString("x2") }) -join ""
```

Gerar `JWT_SECRET`:

```powershell
$bytes = New-Object byte[] 32
[System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
($bytes | ForEach-Object { $_.ToString("x2") }) -join ""
```

Use valores diferentes para cada variável.

---

# Atenção ao POSTGRES_PASSWORD

A senha definida em:

```env
POSTGRES_PASSWORD=
```

é utilizada na criação inicial do banco PostgreSQL.

Depois que o banco já foi criado e o volume Docker já existe, **não altere apenas a senha no `.env`**.

Se isso acontecer, o backend poderá apresentar erro semelhante a:

```text
password authentication failed for user "eco_user"
```

Isso ocorre porque o banco continua utilizando a senha com a qual foi criado anteriormente.

Em uma instalação existente, a troca da senha deve ser feita de forma coordenada no PostgreSQL e no `.env`.

Em ambiente local descartável, também é possível apagar o volume e recriar o banco, mas isso remove todos os dados.

---

# Configuração do primeiro administrador

Antes de iniciar a aplicação, configure:

```env
ADMIN_EMAIL=
ADMIN_PASSWORD=
ADMIN_NAME=Administrador
```

Exemplo:

```env
ADMIN_EMAIL=admin@eco.com
ADMIN_PASSWORD=ecos2026@
ADMIN_NAME=Administrador
```

Na primeira inicialização, o backend cria automaticamente o administrador configurado.

O comportamento é:

- se `ADMIN_EMAIL` ou `ADMIN_PASSWORD` não estiver configurado, o administrador não é criado;
- se o usuário ainda não existir, ele é criado;
- se já existir, não é duplicado;
- a senha de um usuário existente não é alterada automaticamente.

Depois disso, os demais usuários podem ser administrados pela própria aplicação.

Em ambiente oficial, utilize credenciais próprias e seguras.

---

# Configuração do CORS

Em execução local:

```env
CORS_ORIGINS=http://localhost:4200
```

Quando a aplicação estiver disponível em outro endereço, altere para o endereço real do frontend.

Exemplo:

```env
CORS_ORIGINS=https://sistema.exemplo.com
```

---

# Conferindo as configurações

Antes de iniciar a aplicação, é possível verificar como o Docker Compose interpretou o `.env`:

```bash
docker compose config
```

Confira principalmente:

```text
POSTGRES_DB
POSTGRES_USER
POSTGRES_PASSWORD
DATABASE_URL
JWT_SECRET
CORS_ORIGINS
ADMIN_EMAIL
ADMIN_NAME
```

A senha utilizada na `DATABASE_URL` deve corresponder ao `POSTGRES_PASSWORD`.

> Atenção: `docker compose config` pode exibir senhas e chaves no terminal. Não compartilhe essa saída em locais públicos.

---

# Iniciar a aplicação

Na raiz do projeto:

```bash
docker compose up -d --build
```

O comando:

1. cria o banco PostgreSQL;
2. inicia o backend;
3. executa automaticamente as migrations;
4. cria o primeiro administrador, caso configurado;
5. inicia o frontend.

---

# Verificar se os serviços estão funcionando

Execute:

```bash
docker compose ps
```

Resultado esperado:

```text
eco-control-db          healthy
eco-control-backend     healthy
eco-control-frontend    running
```

---

# Endereços padrão

## Frontend

```text
http://localhost:4200
```

## Backend

```text
http://localhost:8001
```

## Swagger

```text
http://localhost:8001/docs
```

## Health check

```text
http://localhost:8001/health
```

## PostgreSQL

```text
Host: localhost
Porta: 5433
Banco: eco_control
Usuário: eco_user
```

---

# Verificar a API

### Linux

```bash
curl http://localhost:8001/health
```

### Windows PowerShell

```powershell
Invoke-WebRequest http://localhost:8001/health
```

---

# Verificar migrations

```bash
docker compose exec backend alembic current
```

A migration deve aparecer como `head`.

Atualmente:

```text
0008 (head)
```

---

# Instalação nova

Uma instalação nova **não carrega ECOs fictícias automaticamente**.

Ao iniciar o projeto:

```bash
docker compose up -d --build
```

o sistema:

1. cria o PostgreSQL;
2. executa as migrations;
3. cria as tabelas;
4. inicia o backend;
5. cria o administrador configurado;
6. inicia o frontend.

As ECOs permanecem vazias até que dados sejam inseridos pela aplicação ou pelas integrações autorizadas.

Para verificar:

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

# Dados padrão

As migrations podem cadastrar configurações necessárias para o funcionamento da aplicação.

Atualmente:

- migration `0007`: mapeamentos padrão OBU → AU;
- migration `0008`: mapeamentos padrão Owner → Group.

Esses registros fazem parte da configuração inicial do sistema.

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

O seed não é executado automaticamente pelo `docker-compose.yml`.

---

# Parar a aplicação

Para parar os containers preservando o banco:

```bash
docker compose down
```

Os dados permanecem armazenados no volume Docker.

---

# Iniciar novamente

Quando os containers já existem:

```bash
docker compose up -d
```

Caso tenha ocorrido alteração no código:

```bash
docker compose up -d --build
```

---

# Atualizar o projeto em uma máquina que já possui o sistema

Primeiro verifique:

```bash
git status
```

Se não houver alterações locais pendentes:

```bash
git fetch origin
git pull origin nome-da-branch
```

Depois:

```bash
docker compose up -d --build
```

Confira:

```bash
docker compose ps
```

E, se necessário:

```bash
docker compose logs backend --tail 100
```

As migrations são executadas automaticamente na inicialização do backend.

---

# Atenção ao volume do PostgreSQL

O banco de dados é armazenado em um volume Docker.

O comando:

```bash
docker compose down
```

preserva os dados.

Já:

```bash
docker compose down -v
```

remove o volume do banco.

Isso significa que **todos os dados armazenados serão apagados**.

Não utilize `docker compose down -v` em um ambiente com dados que precisam ser preservados.

---

# Backup do banco

Antes de operações que possam afetar os dados, é recomendado realizar um backup.

```bash
docker compose exec -T db pg_dump -U eco_user -d eco_control > eco_control_backup.sql
```

Para restaurar:

```bash
docker compose exec -T db psql -U eco_user -d eco_control < eco_control_backup.sql
```

Em ambiente oficial, siga também a política de backup definida pela infraestrutura.

---

# Logs

## Backend

```bash
docker compose logs backend --tail 100
```

## Frontend

```bash
docker compose logs frontend --tail 100
```

## Banco

```bash
docker compose logs db --tail 100
```

## Todos os serviços

```bash
docker compose logs -f
```

## Backend em tempo real

```bash
docker compose logs -f backend
```

---

# Problemas comuns

## Backend aparece como unhealthy

Execute:

```bash
docker compose logs backend --tail 200
```

Verifique principalmente:

- conexão com o banco;
- configurações do `.env`;
- migrations;
- portas em uso;
- erros durante a inicialização.

---

## Erro de senha do PostgreSQL

Exemplo:

```text
password authentication failed for user "eco_user"
```

Confira:

```bash
docker compose config
```

Verifique se o backend e o PostgreSQL estão utilizando a mesma senha.

Se o volume foi criado com uma senha antiga, alterar somente o `.env` não altera a senha interna do banco.

---

## Conflito de nome de container

Exemplo:

```text
Conflict. The container name "/eco-control-db" is already in use
```

Verifique:

```bash
docker ps -a
```

Em ambiente local, confirme se são containers antigos do mesmo projeto antes de removê-los.

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

Os serviços também podem ser executados separadamente.

## Banco

```bash
docker compose up -d db
```

## Backend

```powershell
cd server
.\.venv\Scripts\Activate.ps1
alembic upgrade head
uvicorn main:app --reload --port 8001
```

## Frontend

```bash
cd client
npm install
npm start
```

Para uma execução completa e padronizada, prefira:

```bash
docker compose up -d --build
```

---

# Segurança

Nunca versione:

- `.env`;
- senhas reais;
- tokens;
- JWT secrets;
- chaves privadas;
- dados sensíveis;
- dumps de banco.

Em ambiente oficial:

- gere um `POSTGRES_PASSWORD` forte;
- gere um `JWT_SECRET` aleatório;
- configure credenciais próprias para o administrador;
- configure corretamente o `CORS_ORIGINS`;
- utilize HTTPS quando houver acesso externo;
- mantenha os segredos apenas no servidor;
- mantenha backups do banco.

---

# Resumo para executar em uma nova máquina

```bash
git clone https://github.com/KarolVSDev/eco-control.git
cd eco-control
cp .env.example .env
```

Depois:

1. configure o `.env`;
2. gere `POSTGRES_PASSWORD` e `JWT_SECRET` se for um ambiente oficial;
3. configure o administrador;
4. configure o CORS;
5. execute:

```bash
docker compose up -d --build
```

6. verifique:

```bash
docker compose ps
```

7. acesse:

```text
http://localhost:4200
```

---

# Repositório

```text
https://github.com/KarolVSDev/eco-control
```