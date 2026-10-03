# Histórico de Migração — Base44 para ECO CONTROL

Este documento registra a evolução do **ECO CONTROL** a partir de um protótipo desenvolvido no Base44 para uma aplicação com frontend Angular, backend FastAPI e persistência PostgreSQL.

O objetivo da migração foi transformar o protótipo em uma aplicação com arquitetura própria, código versionado e maior controle sobre regras de negócio, autenticação, persistência e evolução técnica.

---

## 1. Contexto

O Base44 foi utilizado inicialmente como referência para:

- estrutura visual;
- organização das telas;
- fluxos principais;
- validação inicial do conceito do ECO CONTROL.

A implementação atual não depende do Base44 para sua execução.

O projeto passou a possuir código próprio para:

```text
Frontend
Backend
Banco de dados
Autenticação
Permissões
Regras de negócio
Importação
Exportação
Auditoria
```

---

# 2. Arquitetura Atual

A aplicação atualmente utiliza:

```text
Angular 18
    ↓
FastAPI
    ↓
SQLAlchemy
    ↓
PostgreSQL 16
```

A evolução deixou de concentrar o comportamento somente no protótipo visual e passou a separar responsabilidades entre diferentes camadas.

---

# 3. Frontend

O frontend foi implementado em:

```text
Angular 18
```

com TypeScript.

Entre os recursos utilizados estão:

```text
Angular Router
Reactive Forms
HttpClient
Route Guards
HttpInterceptor
RxJS
```

A aplicação está localizada em:

```text
client/
```

---

# 4. Formulários

Os formulários passaram a utilizar recursos do Angular, incluindo:

```text
ReactiveFormsModule
```

Isso permite que validações de interface sejam realizadas antes da comunicação com o backend.

Entretanto, a validação definitiva continua sendo responsabilidade da API.

---

# 5. Navegação e Controle de Acesso

A aplicação Angular possui:

```text
authGuard
adminGuard
```

para controlar a navegação de acordo com o estado de autenticação e o perfil do usuário.

Esses mecanismos atuam no frontend.

O backend continua validando todas as operações protegidas.

---

# 6. Interceptor de Autenticação

Foi implementado um:

```text
HttpInterceptor
```

que adiciona automaticamente:

```http
Authorization: Bearer <token>
```

às chamadas autenticadas.

O interceptor também trata:

```text
401 Unauthorized
```

realizando logout local e redirecionando para:

```text
/login
```

---

# 7. Backend FastAPI

As regras da aplicação passaram a ser disponibilizadas através de uma API construída com:

```text
FastAPI
```

O backend está localizado em:

```text
server/
```

e possui separação entre:

```text
Controllers
Schemas
Services
Repositories
Models
Utilities
```

---

# 8. Controllers

Os controllers são responsáveis pela exposição das rotas HTTP.

Exemplos de áreas atualmente atendidas:

```text
auth
ecos
dashboard
history
usuários
permissões
settings
```

---

# 9. Schemas Pydantic

Os payloads são validados através do Pydantic.

Essa camada define:

- tipos;
- campos aceitos;
- limites;
- estruturas de entrada;
- estruturas de saída.

O schema das ECOs utiliza proteção contra campos não previstos através de:

```text
extra = forbid
```

---

# 10. Service Layer

As regras de negócio foram centralizadas em serviços específicos.

Entre elas estão:

```text
criação de ECO
atualização de ECO
permissões
ITEM/POSITION
OBU → AU
OWNER → GROUP
importação XLSX
histórico
dashboard
configurações
usuários
```

Isso evita concentrar as regras diretamente nos componentes do frontend.

---

# 11. Repository Layer

Os repositórios encapsulam operações de persistência utilizando SQLAlchemy.

Fluxo:

```text
Controller
 ↓
Service
 ↓
Repository
 ↓
SQLAlchemy
 ↓
PostgreSQL
```

Essa organização facilita manutenção e separação de responsabilidades.

---

# 12. Banco de Dados

O projeto utiliza atualmente:

```text
PostgreSQL 16
```

A persistência é realizada por meio do SQLAlchemy.

Entre as entidades principais estão:

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

# 13. UUID

As entidades principais utilizam:

```text
UUID
```

como identificador interno.

Isso é utilizado, por exemplo, em:

```text
users.id
ecos.id
eco_history.id
```

---

# 14. Evolução do Schema

O controle de versão do banco utiliza:

```text
Alembic
```

As migrations atuais incluem:

```text
0001_initial
0002_preserve_eco_history_id
0003_remove_eco_text_limits
```

---

# 15. Preservação do Histórico

Uma das evoluções do banco foi garantir que o histórico permaneça disponível mesmo após a exclusão de uma ECO.

A migration:

```text
0002_preserve_eco_history_id
```

alterou essa relação para preservar os registros de auditoria.

---

# 16. Preservação dos Textos Importados

A estrutura original possuía limites de tamanho em vários campos textuais.

A migration:

```text
0003_remove_eco_text_limits
```

converteu diversos campos para:

```text
TEXT
```

Isso reduz o risco de:

```text
truncamento
rejeição por tamanho
perda de conteúdo importado
```

especialmente em informações originadas da `CTRL GERAL`.

---

# 17. Importação da CTRL GERAL

O sistema possui atualmente um fluxo próprio para importação de planilhas XLSX.

O processo é:

```text
Upload XLSX
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

O preview não persiste alterações.

---

# 18. Importação Transacional

A importação definitiva é executada de forma transacional.

Regra:

```text
ERROR
 ↓
cancela lote
```

```text
DUPLICATE
 ↓
ignora
```

```text
NEW
 ↓
insere
```

Se ocorrer erro durante a persistência:

```text
rollback
```

é executado.

---

# 19. Exportação

O ECO CONTROL também possui exportação da CTRL GERAL em formato:

```text
XLSX
```

A exportação utiliza os filtros da aplicação e inclui campos calculados pelo backend.

---

# 20. Campos Calculados

Diversos valores originalmente representados por fórmulas da planilha são calculados pelo backend.

A lógica está centralizada em:

```text
server/app/utils/eco_calculations.py
```

Entre os valores calculados estão:

```text
GAP
Delay ECO Register
ECO Registration Week
GAP Agreement
AZ Gap
Release Week
Release Month
Release Year
```

entre outros indicadores derivados.

---

# 21. Mapeamento OBU → AU

A relação:

```text
OBU → AU
```

foi transformada em configuração persistida no banco.

Tabela:

```text
obu_au_mappings
```

Isso permite que a lógica seja atualizada sem necessidade de espalhar valores fixos pela interface.

---

# 22. Mapeamento OWNER → GROUP

Da mesma forma, a relação:

```text
OWNER → GROUP
```

é armazenada em:

```text
owner_group_mappings
```

Quando apropriado, o backend utiliza esse mapeamento durante criação e atualização das ECOs.

---

# 23. Autenticação

A aplicação passou a possuir autenticação própria.

O fluxo utiliza:

```text
e-mail
senha
JWT
```

O backend valida a senha armazenada em hash e gera um token JWT.

O frontend utiliza o token nas chamadas posteriores.

---

# 24. Permissões

Além dos perfis:

```text
admin
analyst
```

o sistema possui permissões específicas para analistas.

Permissões gerais:

```text
can_create_eco
can_bulk_edit
can_view_history
```

Permissões por campo:

```text
can_view
can_edit
```

Assim, o controle de acesso não depende apenas de elementos visuais do frontend.

---

# 25. Auditoria

Criações, alterações e exclusões de ECOs são registradas em:

```text
eco_history
```

Os registros contêm informações como:

```text
ECO
ITEM
campo
valor anterior
valor novo
usuário
ação
data
```

---

# 26. Exclusão de ECOs

A aplicação atual possui:

```text
exclusão individual
exclusão múltipla
```

ambas restritas a administradores.

Após uma exclusão, o backend reorganiza:

```text
ITEM
POSITION
```

mantendo a sequência da tabela.

---

# 27. Dashboard

O backend passou a fornecer endpoints próprios para alimentar:

```text
cards
agrupamentos
evolução
indicadores temporais
resumo mensal
```

O frontend consome esses dados através da API.

---

# 28. Docker

No ambiente atual, o Docker Compose é utilizado para o banco PostgreSQL.

```text
docker compose up -d db
```

O `docker-compose.yml` atual não executa o frontend e o backend.

Eles são executados diretamente nos ambientes:

```text
Angular → npm
FastAPI → Uvicorn
```

---

# 29. Ambiente Atual de Desenvolvimento

O fluxo recomendado é:

```text
PostgreSQL
 ↓
Docker Compose

FastAPI
 ↓
Python / Uvicorn

Angular
 ↓
Node / npm
```

---

# 30. Estrutura Atual

```text
eco-control/
│
├── client/
│   └── Angular 18
│
├── server/
│   ├── FastAPI
│   ├── SQLAlchemy
│   ├── Alembic
│   └── testes
│
├── docs/
│
└── docker-compose.yml
```

---

# 31. Resultado da Migração

A evolução do protótipo resultou em uma aplicação com responsabilidades separadas:

```text
Interface
 ↓
Angular

Integração e regras
 ↓
FastAPI

Persistência
 ↓
PostgreSQL

Evolução do banco
 ↓
Alembic

Autorização
 ↓
JWT + permissões

Auditoria
 ↓
eco_history
```

---

# 32. Base44 como Referência

O Base44 permanece relevante como parte do histórico do projeto e como referência do protótipo inicial.

Entretanto, a aplicação atual deve utilizar como fontes técnicas de verdade:

```text
código da branch develop
schemas FastAPI
models SQLAlchemy
migrations Alembic
documentação em docs/
```

Alterações futuras devem manter esses elementos sincronizados.

---

# 33. Evolução Futura

Novas funcionalidades devem preferencialmente reutilizar a arquitetura existente.

Exemplo:

```text
Nova funcionalidade
       ↓
Angular
       ↓
API FastAPI
       ↓
Service
       ↓
Repository
       ↓
PostgreSQL
```

Isso ajuda a manter:

- regras centralizadas;
- autenticação;
- autorização;
- auditoria;
- consistência de dados;
- manutenção do projeto.

A documentação deve acompanhar a evolução da implementação.