# Arquitetura do Sistema — ECO CONTROL

Este documento descreve a arquitetura atual do **ECO CONTROL**, incluindo a separação entre frontend, backend e banco de dados, a organização das camadas internas e a infraestrutura utilizada no ambiente local de desenvolvimento.

---

## 1. Visão Geral

O ECO CONTROL utiliza uma arquitetura composta por:

```text
SPA Angular
    ↓
API REST FastAPI
    ↓
SQLAlchemy
    ↓
PostgreSQL
```

O frontend não acessa diretamente o banco de dados.

Toda regra de negócio, persistência, autorização e auditoria passa pelo backend.

---

## 2. Arquitetura Geral

```text
+------------------------------------------------------------------+
|                         FRONTEND                                 |
|                         Angular 18                               |
|                                                                  |
| Components / Pages                                               |
|        ↓                                                         |
| Services HTTP                                                    |
|        ↓                                                         |
| Guards / Interceptors                                            |
+------------------------------------------------------------------+
                           |
                           | HTTP / JSON
                           | Authorization: Bearer JWT
                           v
+------------------------------------------------------------------+
|                         BACKEND                                  |
|                         FastAPI                                  |
|                                                                  |
| Controllers / Routers                                            |
|        ↓                                                         |
| Pydantic Schemas                                                 |
|        ↓                                                         |
| Services                                                         |
|        ↓                                                         |
| Repositories                                                     |
|        ↓                                                         |
| SQLAlchemy                                                       |
+------------------------------------------------------------------+
                           |
                           v
+------------------------------------------------------------------+
|                       POSTGRESQL 16                              |
|                                                                  |
| ECOs                                                             |
| Usuários                                                         |
| Histórico                                                        |
| Permissões                                                       |
| Mapeamentos                                                      |
| Configurações                                                    |
+------------------------------------------------------------------+
```

---

# 3. Frontend

O frontend está localizado em:

```text
client/
```

A aplicação utiliza:

```text
Angular 18
TypeScript
RxJS
Reactive Forms
Angular Router
HttpClient
```

A versão atual das dependências Angular é da linha:

```text
18.2.x
```

---

# 4. Responsabilidades do Frontend

O frontend é responsável principalmente por:

- apresentação das telas;
- formulários;
- tabelas;
- filtros;
- dashboards;
- navegação;
- experiência do usuário;
- integração HTTP com a API;
- armazenamento da sessão local;
- aplicação visual das permissões;
- upload e download de arquivos.

As regras críticas não devem depender exclusivamente do Angular.

---

# 5. Comunicação com a API

A URL utilizada no ambiente local é:

```text
http://localhost:8000/api/v1
```

As chamadas comuns utilizam:

```text
application/json
```

Uploads XLSX utilizam:

```text
multipart/form-data
```

A autenticação utiliza:

```http
Authorization: Bearer <token>
```

---

# 6. Autenticação no Frontend

O Angular possui:

```text
AuthService
AuthInterceptor
authGuard
adminGuard
```

O `AuthService` mantém:

```text
eco_token
eco_user
```

no `localStorage`.

O `AuthInterceptor` injeta o JWT nas requisições e trata respostas `401`.

---

# 7. Backend

O backend está localizado em:

```text
server/
```

e utiliza:

```text
Python
FastAPI
Pydantic
SQLAlchemy
PostgreSQL
Alembic
```

A aplicação FastAPI é inicializada em:

```text
server/main.py
```

---

# 8. Controllers

Os controllers expõem os endpoints HTTP.

Atualmente existem módulos para:

```text
auth
ecos
dashboard
history
administração
settings
```

Estrutura:

```text
server/app/controller/
```

Os controllers devem permanecer responsáveis principalmente por:

```text
receber requisição
validar parâmetros HTTP
acionar serviço
devolver resposta
```

e não concentrar regras extensas de negócio.

---

# 9. Schemas Pydantic

Os schemas ficam em:

```text
server/app/schemas/
```

Eles definem:

- estrutura dos payloads;
- tipos;
- campos obrigatórios;
- limites;
- validações;
- estrutura de entrada e saída.

Por exemplo, uma atualização de ECO utiliza schemas que rejeitam campos desconhecidos através de:

```text
extra = forbid
```

Isso reduz o risco de dados inesperados entrarem na aplicação.

---

# 10. Service Layer

A camada de serviços está localizada em:

```text
server/app/services/
```

Ela concentra regras como:

- permissões;
- criação e atualização de ECOs;
- ITEM e POSITION;
- OBU → AU;
- OWNER → GROUP;
- histórico;
- importação XLSX;
- usuários;
- configurações;
- dashboard.

Fluxo:

```text
Controller
   ↓
Service
   ↓
Repository
```

---

# 11. Repository Layer

A camada de repositórios está localizada em:

```text
server/app/repository/
```

Ela encapsula consultas e operações de persistência.

Entre os repositórios estão componentes relacionados a:

```text
ECO
histórico
permissões
settings
```

Essa separação evita que regras de negócio dependam diretamente de consultas SQL espalhadas pela aplicação.

---

# 12. ORM e Sessões

A aplicação utiliza SQLAlchemy de forma síncrona.

A configuração principal utiliza:

```python
create_engine(...)
sessionmaker(...)
```

Portanto, a arquitetura atual não utiliza um driver SQLAlchemy assíncrono.

Fluxo:

```text
FastAPI
 ↓
SQLAlchemy Session
 ↓
PostgreSQL
```

---

# 13. Banco de Dados

O banco utilizado é:

```text
PostgreSQL 16
```

No ambiente local, o Docker Compose utiliza:

```text
postgres:16-alpine
```

O PostgreSQL contém tabelas relacionadas a:

```text
users
ecos
eco_history
analyst_permissions
field_permissions
obu_au_mappings
owner_group_mappings
managers
```

---

# 14. Docker Compose

Atualmente o `docker-compose.yml` é utilizado para executar o PostgreSQL local.

Fluxo:

```text
docker compose up -d db
```

O Docker Compose atual não executa toda a aplicação.

Frontend e backend são executados diretamente nos respectivos ambientes de desenvolvimento.

---

# 15. Execução Local

Arquitetura atual de execução:

```text
Terminal 1
PostgreSQL via Docker Compose

Terminal 2
FastAPI via Uvicorn

Terminal 3
Angular via npm
```

Exemplo:

```text
docker compose up -d db
```

```text
uvicorn main:app --reload --port 8000
```

```text
npm start
```

---

# 16. Alembic

A evolução do schema é controlada através do:

```text
Alembic
```

As migrations ficam em:

```text
server/alembic/versions/
```

O histórico atual inclui:

```text
0001_initial
0002_preserve_eco_history_id
0003_remove_eco_text_limits
```

---

# 17. Autenticação

O backend utiliza:

```text
JWT Bearer Token
```

O fluxo é:

```text
Login
 ↓
FastAPI valida senha
 ↓
JWT
 ↓
Angular
 ↓
Authorization Bearer
 ↓
current_user
```

Os tokens são assinados utilizando:

```text
HS256
```

---

# 18. Autorização

A autorização combina:

```text
role
+
permissões gerais
+
permissões por campo
```

Administradores possuem acesso administrativo.

Analistas podem possuir:

```text
can_create_eco
can_bulk_edit
can_view_history
```

e:

```text
can_view
can_edit
```

para campos individuais.

---

# 19. Auditoria

Alterações de ECO geram registros na tabela:

```text
eco_history
```

Entre as ações registradas estão:

```text
created
updated
deleted
```

A arquitetura foi ajustada para manter o histórico disponível mesmo após a exclusão da ECO original.

---

# 20. Importação XLSX

A importação possui uma etapa de preview e uma etapa de persistência.

```text
XLSX
 ↓
Preview
 ↓
Validação
 ↓
NEW / DUPLICATE / ERROR
 ↓
Importação
 ↓
PostgreSQL
```

O processo definitivo utiliza transação.

Em caso de falha:

```text
rollback
```

é executado.

---

# 21. Exportação XLSX

O backend gera arquivos da `CTRL GERAL` através de:

```text
GET /api/v1/ecos/export
```

A exportação considera:

- filtros;
- dados persistidos;
- campos calculados.

---

# 22. Campos Calculados

Os cálculos derivados da CTRL GERAL ficam centralizados em:

```text
server/app/utils/eco_calculations.py
```

e não precisam ser duplicados no frontend ou persistidos desnecessariamente.

Isso inclui:

```text
GAP
AZ Gap
Delay
Release Week
Release Month
Release Year
demais indicadores temporais
```

---

# 23. Mapeamentos de Domínio

O sistema utiliza configurações persistidas para:

```text
OBU → AU
OWNER → GROUP
```

Essas relações ficam no banco e podem ser administradas através da API.

Isso evita manter essas regras espalhadas pelo frontend.

---

# 24. Fluxo de Atualização de ECO

```text
Angular
 ↓
PATCH /ecos/{id}
 ↓
Controller
 ↓
Pydantic
 ↓
EcoService
 ↓
Permissões
 ↓
OBU → AU / OWNER → GROUP
 ↓
Repository / SQLAlchemy
 ↓
Histórico
 ↓
Commit
```

---

# 25. Fluxo de Importação

```text
Angular
 ↓
arquivo XLSX
 ↓
FastAPI
 ↓
EcoImportService
 ↓
leitura CTRL GERAL
 ↓
normalização
 ↓
validação
 ↓
classificação das linhas
 ↓
transação
 ↓
PostgreSQL
```

---

# 26. Tratamento de Falhas

Operações que alteram múltiplos registros devem manter consistência transacional.

O padrão utilizado é:

```text
try
 ↓
alterações
 ↓
commit

erro
 ↓
rollback
```

Isso é especialmente importante em:

```text
importação
exclusão
exclusão múltipla
reorganização de ITEM/POSITION
```

---

# 27. Configuração por Ambiente

Configurações são carregadas através de:

```text
pydantic-settings
```

e podem ser definidas em:

```text
.env
```

Entre elas estão:

```text
database_url
jwt_secret
access_token_minutes
cors_origins
```

Arquivos `.env` não devem ser versionados.

---

# 28. CORS

O FastAPI utiliza:

```text
CORSMiddleware
```

As origens autorizadas são configuradas através de:

```text
cors_origins
```

No ambiente local, o frontend normalmente utiliza:

```text
http://localhost:4200
```

---

# 29. Organização Geral do Projeto

```text
eco-control/
│
├── client/
│   └── Angular
│
├── server/
│   ├── main.py
│   ├── app/
│   │   ├── config/
│   │   ├── controller/
│   │   ├── models/
│   │   ├── repository/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── utils/
│   │
│   └── alembic/
│
├── docs/
│
├── docker-compose.yml
└── README.md
```

---

# 30. Princípios Arquiteturais

A implementação atual segue os seguintes princípios:

```text
Frontend não acessa banco diretamente
Backend valida regras
Backend valida permissões
Banco mantém persistência
Alembic controla schema
Histórico registra alterações
Campos calculados permanecem centralizados
```

---

# 31. Evolução

Novos componentes, integrações ou automações devem preferencialmente reutilizar a API e as camadas existentes em vez de acessar diretamente o PostgreSQL.

Fluxo recomendado:

```text
Novo componente
      ↓
API / Service
      ↓
Regras existentes
      ↓
PostgreSQL
```

Isso ajuda a preservar:

- consistência;
- permissões;
- auditoria;
- regras de negócio;
- rastreabilidade.

A implementação existente na branch `develop` é a referência principal para esta documentação.