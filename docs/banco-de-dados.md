# Modelo de Dados Relacional e Persistência — ECO CONTROL

Este documento descreve o modelo de dados atualmente utilizado pelo sistema **ECO CONTROL**, incluindo as entidades persistidas no PostgreSQL, os relacionamentos lógicos, as permissões, os mapeamentos de configuração, o histórico de auditoria e o controle de evolução do banco por meio do Alembic.

A documentação deve permanecer alinhada à implementação disponível na branch `develop`.

---

## 1. Tecnologias de Persistência

O backend utiliza:

- **PostgreSQL 16** como banco de dados relacional;
- **SQLAlchemy** para mapeamento objeto-relacional;
- **Alembic** para controle de versão do schema;
- **UUID** como identificador principal das entidades;
- **Docker Compose** para execução local do PostgreSQL.

No ambiente local, o PostgreSQL é disponibilizado pelo serviço:

```yaml
postgres:16-alpine
```

Configuração padrão de desenvolvimento:

```text
Host: localhost
Porta: 5433
Banco: eco_control
Usuário: eco_user
```

As credenciais utilizadas localmente são destinadas somente ao ambiente de desenvolvimento.

---

# 2. Visão Geral das Entidades

Atualmente, o ECO CONTROL possui as seguintes entidades principais:

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

Visão conceitual:

```text
+---------------------------+
|           users           |
+---------------------------+
| id (UUID)                 |
| email                     |
| full_name                 |
| hashed_password           |
| role                      |
| active                    |
| created_at                |
+---------------------------+

            |
            | permissões associadas por e-mail
            |
            v

+---------------------------+
|   analyst_permissions     |
+---------------------------+
| id (UUID)                 |
| user_email                |
| can_create_eco            |
| can_bulk_edit             |
| can_view_history          |
+---------------------------+

+---------------------------+
|     field_permissions     |
+---------------------------+
| id (UUID)                 |
| user_email                |
| field_key                 |
| can_view                  |
| can_edit                  |
+---------------------------+


+---------------------------+
|            ecos           |
+---------------------------+
| id (UUID)                 |
| item                      |
| position                  |
| month                     |
| ... dados CTRL GERAL ...  |
| created_at                |
| updated_at                |
+---------------------------+

            |
            | gera registros de auditoria
            v

+---------------------------+
|       eco_history         |
+---------------------------+
| id (UUID)                 |
| eco_id                    |
| eco_code                  |
| item                      |
| field_key                 |
| field_label               |
| old_value                 |
| new_value                 |
| user_email                |
| user_name                 |
| action                    |
| created_at                |
+---------------------------+


+---------------------------+
|     obu_au_mappings       |
+---------------------------+
| id (UUID)                 |
| obu                       |
| au                        |
+---------------------------+


+---------------------------+
|  owner_group_mappings     |
+---------------------------+
| id (UUID)                 |
| owner                     |
| group_name                |
+---------------------------+


+---------------------------+
|         managers          |
+---------------------------+
| id (UUID)                 |
| name                      |
+---------------------------+
```

---

# 3. Tabela `users`

A tabela `users` armazena os usuários autorizados a acessar o ECO CONTROL.

## Campos

| Campo | Tipo | Regra |
|---|---|---|
| `id` | UUID | Chave primária |
| `email` | VARCHAR(255) | Único e indexado |
| `full_name` | VARCHAR(255) | Nome completo |
| `hashed_password` | VARCHAR(255) | Hash da senha |
| `role` | VARCHAR(20) | Perfil do usuário |
| `active` | BOOLEAN | Indica se a conta está ativa |
| `created_at` | TIMESTAMP WITH TIME ZONE | Data de criação |

Os perfis atualmente utilizados pela aplicação são:

```text
admin
analyst
```

A autenticação é realizada utilizando o e-mail do usuário.

As senhas não são armazenadas em texto puro.

---

# 4. Tabela `ecos`

A tabela `ecos` armazena os dados persistidos das ECOs e corresponde aos principais campos existentes na planilha `CTRL GERAL`.

O identificador interno utiliza UUID.

```text
id
```

Além dele, `ITEM` e `POSITION` são utilizados para controlar a sequência lógica e a posição dos registros.

---

## 4.1. Controle e identificação

| Campo | Tipo |
|---|---|
| `id` | UUID |
| `item` | INTEGER |
| `position` | INTEGER |
| `month` | VARCHAR(8) |
| `product` | TEXT |
| `obu` | TEXT |
| `au` | VARCHAR(30) |

`item` possui restrição de unicidade e é utilizado como sequência lógica das ECOs.

`position` auxilia no controle da posição dos registros.

`month` é definido pelo sistema.

`au` pode ser derivado automaticamente através do mapeamento:

```text
OBU → AU
```

---

## 4.2. Classificação

| Campo | Tipo |
|---|---|
| `group_name` | VARCHAR(30) |
| `owner` | TEXT |
| `item_type` | TEXT |
| `eco_type` | TEXT |
| `change_bom` | TEXT |
| `status` | TEXT |
| `receb` | TEXT |

Externamente, a API apresenta:

```text
group
```

enquanto a coluna interna do banco é:

```text
group_name
```

O GROUP pode ser definido automaticamente conforme:

```text
OWNER → GROUP
```

---

# 5. ECO HQ

Os seguintes campos representam informações principais da ECO:

| Campo | Tipo |
|---|---|
| `eco` | TEXT |
| `change_reason` | TEXT |
| `hq_eco_release_date` | DATE |
| `az_eco_register_date` | DATE |
| `auto_ecr` | TEXT |
| `council_meeting_week` | TEXT |

Os campos textuais provenientes da planilha são armazenados como `TEXT` quando necessário para evitar truncamento das informações originais.

---

# 6. Dados de Origem

A tabela suporta até três conjuntos de informações de origem.

### Origem 1

```text
hz_in_kr_eco_1
hz_sh_in_receive_date_1
```

### Origem 2

```text
hz_in_kr_eco_2
hz_sh_in_receive_date_2
```

### Origem 3

```text
hz_in_kr_eco_3
hz_sh_in_receive_date_3
```

Tipos:

| Campo | Tipo |
|---|---|
| `hz_in_kr_eco_1` | TEXT |
| `hz_sh_in_receive_date_1` | DATE |
| `hz_in_kr_eco_2` | TEXT |
| `hz_sh_in_receive_date_2` | DATE |
| `hz_in_kr_eco_3` | TEXT |
| `hz_sh_in_receive_date_3` | DATE |

---

# 7. AZ ECO

Campos relacionados ao processo AZ ECO:

| Campo | Tipo |
|---|---|
| `az_eco_no` | TEXT |
| `change_reason2` | TEXT |
| `change_bom_az` | TEXT |
| `az_eco_creation_date` | DATE |

---

# 8. Agreement Other Departments

O banco possui três possíveis períodos de Agreement.

### Agreement 1

```text
agreement_start_1
agreement_finish_1
```

### Agreement 2

```text
agreement_start_2
agreement_finish_2
```

### Agreement 3

```text
agreement_start_3
agreement_finish_3
```

Todos os campos desse grupo possuem tipo:

```text
DATE
```

Os respectivos GAPs são calculados pelo backend e não são armazenados diretamente como colunas físicas.

---

# 9. R&D Approval

Campos relacionados ao processo de aprovação R&D:

| Campo | Tipo |
|---|---|
| `second_aprov_rd` | TEXT |
| `second_aprov_rd_start_1` | DATE |
| `second_aprov_rd_finish_1` | DATE |
| `second_aprov_rd_start_2` | DATE |
| `second_aprov_rd_finish_2` | DATE |

Os GAPs relacionados a R&D também são calculados dinamicamente.

---

# 10. Campos Adicionais

| Campo | Tipo |
|---|---|
| `change_reason_az` | TEXT |
| `model_az` | TEXT |
| `new_model` | TEXT |
| `origem_approval` | TEXT |
| `event` | TEXT |
| `comments` | TEXT |

Os campos textuais não possuem limite artificial relacionado ao tamanho original da planilha.

Essa decisão evita perda ou truncamento de informações, principalmente em:

```text
COMMENTS
MODEL AZ
CHANGE REASON
```

e outros campos que podem possuir conteúdo extenso.

---

# 11. SET ECO

Campos relacionados ao SET ECO:

| Campo | Tipo |
|---|---|
| `set_eco` | TEXT |
| `set_eco_register_date` | DATE |
| `set_eco_release_date` | DATE |
| `set_eco_change_reason` | TEXT |
| `set_eco_model` | TEXT |

---

# 12. Campos de Auditoria da ECO

Cada ECO também possui:

| Campo | Tipo |
|---|---|
| `created_at` | TIMESTAMP WITH TIME ZONE |
| `updated_at` | TIMESTAMP WITH TIME ZONE |

`created_at` é preenchido automaticamente na criação.

`updated_at` é atualizado automaticamente quando o registro é modificado.

---

# 13. Campos Calculados

Nem todos os campos apresentados no ECO CONTROL correspondem a colunas físicas do banco.

Vários valores são calculados pelo backend utilizando as informações persistidas.

Entre eles estão:

```text
GAP
1-Delay ECO Register
ECO Registration Week

ECO Origem (1)
ECO Origem (2)
ECO Origem (3)

GAP Start AZ ECO
Contar Eco emitida > 1 dias

GAP AGREEMENT
GAP AGREEMENT OTHER DEPTS (1)
GAP AGREEMENT OTHER DEPTS (2)
GAP AGREEMENT OTHER DEPTS (3)
GAP TOTAL AGREEMENT OTHER DEPTS

GAP 2ST APROV R&D (1)
GAP 2ST APROV R&D (2)
GAP TOTAL 2ST APROV R&D

ECO Release Week
AZ Gap

Contar Eco concluída > 7 dias
Contar Eco concluída > 10 dias
Contar Eco concluída > 14 dias

Total Gap
RELEASE MONTH
RELEASE YEAR
```

Esses valores são obtidos por meio da função:

```text
compute_eco_fields()
```

localizada em:

```text
server/app/utils/eco_calculations.py
```

Essa abordagem evita duplicação entre dados persistidos e dados derivados.

---

# 14. Tabela `eco_history`

A tabela `eco_history` armazena a trilha de auditoria das ECOs.

## Campos

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | UUID | Identificador do evento |
| `eco_id` | UUID, nullable | ID original da ECO |
| `eco_code` | VARCHAR(100) | Código da ECO |
| `item` | INTEGER | ITEM no momento da alteração |
| `field_key` | VARCHAR(100) | Identificador interno do campo |
| `field_label` | VARCHAR(160) | Nome amigável |
| `old_value` | TEXT | Valor anterior |
| `new_value` | TEXT | Novo valor |
| `user_email` | VARCHAR(255) | Usuário responsável |
| `user_name` | VARCHAR(255) | Nome do usuário |
| `action` | VARCHAR(20) | Tipo da ação |
| `created_at` | TIMESTAMP WITH TIME ZONE | Data e hora |

Ações utilizadas:

```text
created
updated
deleted
```

---

## 14.1. Preservação do histórico após exclusão

O histórico deve continuar existindo mesmo após a ECO ser excluída.

Por esse motivo, a migration:

```text
0002_preserve_eco_history_id
```

removeu a dependência rígida da chave estrangeira entre:

```text
eco_history.eco_id
```

e:

```text
ecos.id
```

O registro histórico mantém informações independentes, como:

```text
eco_code
item
user_email
field_key
old_value
new_value
action
```

permitindo auditoria mesmo depois da remoção da ECO original.

---

# 15. Tabela `analyst_permissions`

Armazena permissões gerais atribuídas individualmente aos usuários com perfil `analyst`.

## Campos

| Campo | Tipo |
|---|---|
| `id` | UUID |
| `user_email` | VARCHAR(255), UNIQUE |
| `can_create_eco` | BOOLEAN |
| `can_bulk_edit` | BOOLEAN |
| `can_view_history` | BOOLEAN |

### `can_create_eco`

Permite ao analista criar novas ECOs.

### `can_bulk_edit`

Permite operações relacionadas à importação em massa de ECOs.

### `can_view_history`

Permite acessar o histórico de alterações.

Administradores não dependem dessas configurações para executar as operações administrativas.

---

# 16. Tabela `field_permissions`

Controla as permissões de visualização e edição de cada campo para um analista.

## Campos

| Campo | Tipo |
|---|---|
| `id` | UUID |
| `user_email` | VARCHAR(255) |
| `field_key` | VARCHAR(100) |
| `can_view` | BOOLEAN |
| `can_edit` | BOOLEAN |

Existe uma restrição de unicidade para:

```text
(user_email, field_key)
```

Portanto, um mesmo usuário não pode possuir duas configurações distintas para o mesmo campo.

### `can_view`

Define se determinado campo pode ser retornado e exibido para o usuário.

### `can_edit`

Define se o analista pode alterar o campo.

O backend continua sendo responsável pela validação efetiva das permissões.

---

# 17. Tabela `obu_au_mappings`

Armazena as relações utilizadas para cálculo automático de AU.

## Campos

| Campo | Tipo |
|---|---|
| `id` | UUID |
| `obu` | VARCHAR(30), UNIQUE |
| `au` | VARCHAR(30) |

Fluxo:

```text
OBU
 ↓
obu_au_mappings
 ↓
AU
```

Exemplo utilizado no ambiente local:

```text
NWE → GLZ
```

Os valores são configuráveis e não devem ser tratados como uma lista fixa permanente na lógica do sistema.

---

# 18. Tabela `owner_group_mappings`

Armazena as relações utilizadas para preenchimento automático de GROUP.

## Campos

| Campo | Tipo |
|---|---|
| `id` | UUID |
| `owner` | VARCHAR(255), UNIQUE |
| `group_name` | VARCHAR(30) |

Fluxo:

```text
OWNER
  ↓
owner_group_mappings
  ↓
GROUP
```

Quando o OWNER é alterado e nenhum GROUP explícito é informado, o backend pode utilizar esse mapeamento para atualizar o GROUP automaticamente.

---

# 19. Tabela `managers`

Armazena os gerentes configurados no ECO CONTROL.

## Campos

| Campo | Tipo |
|---|---|
| `id` | UUID |
| `name` | VARCHAR(255), UNIQUE |

Essa configuração é administrada por usuários com perfil `admin`.

---

# 20. ITEM e POSITION

O ECO CONTROL possui dois campos importantes para organização dos registros:

```text
ITEM
POSITION
```

## ITEM

Representa a sequência lógica das ECOs.

É único.

## POSITION

Auxilia no controle da posição dos registros.

Ao criar uma ECO abaixo de outra:

```text
POST /api/v1/ecos/{eco_id}/after
```

o backend reorganiza os registros subsequentes.

Exemplo:

```text
ITEM 7
ITEM 8
ITEM 9
```

Inserindo uma nova ECO abaixo do ITEM 7:

```text
ITEM 7
ITEM 8  ← nova ECO
ITEM 9  ← antiga ITEM 8
ITEM 10 ← antiga ITEM 9
```

Ao excluir ECOs, a sequência também é reorganizada.

Na listagem principal, os registros são apresentados por:

```text
ITEM DESC
POSITION DESC
```

---

# 21. Importação da CTRL GERAL

A importação XLSX utiliza os campos persistidos da tabela `ecos`.

Os campos calculados da planilha não são tratados como fonte de verdade.

Fluxo:

```text
Arquivo XLSX
   ↓
CTRL GERAL
   ↓
Parser
   ↓
Normalização
   ↓
Validação
   ↓
Cálculos internos
   ↓
Persistência PostgreSQL
```

As linhas são classificadas como:

```text
NEW
DUPLICATE
ERROR
```

Warnings também podem ser associados às linhas.

Somente registros classificados como `NEW` são persistidos.

A operação definitiva ocorre dentro de uma transação.

Em caso de erro:

```text
rollback
```

é executado.

---

# 22. Textos da planilha

Os campos textuais provenientes da planilha que podem possuir conteúdo variável utilizam `TEXT` no PostgreSQL.

Essa decisão evita problemas como:

```text
value too long for type character varying(...)
```

e, principalmente, impede perda de informação por truncamento.

O sistema não deve reduzir arbitrariamente:

- comentários;
- modelos;
- motivos de alteração;
- textos técnicos;
- identificadores;
- demais conteúdos importados.

---

# 23. Controle de Versão do Banco com Alembic

As alterações estruturais do banco são controladas pelo Alembic.

Diretório:

```text
server/alembic/versions/
```

O histórico atual inclui:

```text
0001_initial.py
0002_preserve_eco_history_id.py
0003_remove_eco_text_limits.py
```

---

## 23.1. Migration `0001_initial`

Responsável pela criação inicial das tabelas definidas no modelo SQLAlchemy.

---

## 23.2. Migration `0002_preserve_eco_history_id`

Ajusta a estrutura do histórico para que registros de auditoria continuem disponíveis após a exclusão da ECO original.

---

## 23.3. Migration `0003_remove_eco_text_limits`

Converte diversos campos textuais da tabela `ecos` de:

```text
VARCHAR(n)
```

para:

```text
TEXT
```

O objetivo é preservar integralmente os dados provenientes da planilha e evitar rejeição ou truncamento de textos extensos.

---

# 24. Comandos Alembic

A partir da pasta:

```text
server/
```

### Aplicar todas as migrations

```bash
alembic upgrade head
```

### Verificar a revisão atual

```bash
alembic current
```

Na versão atual do projeto, a revisão esperada é:

```text
0003
```

### Criar nova migration

```bash
alembic revision -m "descricao_da_alteracao"
```

Quando apropriado, também pode ser utilizado:

```bash
alembic revision --autogenerate -m "descricao_da_alteracao"
```

### Reverter uma migration

```bash
alembic downgrade -1
```

Reversões devem ser realizadas com cuidado, especialmente quando envolverem transformação ou redução de tipos de dados.

---

# 25. Seed de Desenvolvimento

O projeto possui um seed localizado em:

```text
server/app/seed.py
```

A execução é realizada a partir da pasta `server`:

```bash
python -m app.seed
```

O seed é destinado ao ambiente local de desenvolvimento.

---

## 25.1. Usuário administrador

O seed cria:

```text
E-mail: admin@eco.com
Senha: admin123
Role: admin
```

Essas credenciais são destinadas exclusivamente ao ambiente local.

Não devem ser utilizadas em produção.

---

## 25.2. Mapeamentos OBU → AU

O seed inclui exemplos como:

```text
NW1 → GLZ
NWD → GLZ
NWE → GLZ
NWZ → GLZ
NWH → GMZ
NWW → GMZ
NWU → PNZ
NWX → PNZ
NWV → PGZ
NWK → LMZ
NYE → GMZ
```

---

## 25.3. Mapeamentos OWNER → GROUP

O ambiente de desenvolvimento também recebe exemplos de relações OWNER → GROUP.

Esses dados são sintéticos e utilizados somente para facilitar testes locais.

---

## 25.4. ECOs sintéticas

Quando a tabela `ecos` está vazia, o seed cria aproximadamente 30 registros demonstrativos.

Os códigos seguem o padrão:

```text
DEMO00001
DEMO00002
...
```

Esses registros existem somente para auxiliar o desenvolvimento e os testes.

---

# 26. Inicialização local do banco

Na raiz do projeto:

```bash
docker compose up -d db
```

Depois, dentro de:

```text
server/
```

execute:

```bash
alembic upgrade head
```

e:

```bash
python -m app.seed
```

Fluxo completo:

```text
Docker Compose
      ↓
PostgreSQL 16
      ↓
Alembic
      ↓
Schema atualizado
      ↓
Seed
      ↓
Dados locais de desenvolvimento
```

---

# 27. Persistência e Transações

As operações de criação, importação e exclusão que envolvem múltiplos passos utilizam transações.

Fluxo esperado:

```text
Iniciar operação
      ↓
Alterações
      ↓
Validações
      ↓
Tudo correto?
 ┌────┴────┐
 Sim      Não
  ↓         ↓
commit   rollback
```

Isso reduz o risco de manter o banco em um estado parcialmente atualizado.

---

# 28. Segurança dos Dados

Não devem ser versionados no Git:

- bancos locais;
- arquivos `.env`;
- senhas reais;
- tokens JWT;
- chaves privadas;
- planilhas corporativas reais;
- informações sensíveis de produção.

O seed deve utilizar somente dados sintéticos ou explicitamente autorizados.

---

# 29. Manutenção da Documentação

Sempre que ocorrer alteração em:

- `server/app/models/entities.py`;
- migrations Alembic;
- regras de importação;
- permissões;
- mapeamentos;
- histórico;
- criação ou remoção de entidades;

este documento deverá ser atualizado.

O modelo SQLAlchemy e as migrations são as referências técnicas principais para a estrutura efetivamente utilizada pelo banco de dados.