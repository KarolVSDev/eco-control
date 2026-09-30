# Modelo de Dados Relacional e Persistência — ECO CONTROL

Este documento documenta o esquema relacional do banco de dados PostgreSQL, o catálogo das entidades principais, o mecanismo de migrações com Alembic e a carga inicial de dados (*seed*) do sistema **ECO CONTROL**.

---

## 1. Diagrama Entidade-Relacionamento (Textual)

```text
+-----------------------+          +-----------------------+
|         users         | 1      N |     analyst_perms     |
|-----------------------|----------|-----------------------|
| id (PK)               |          | id (PK)               |
| username              |          | user_id (FK -> users) |
| email                 |          | can_approve_exception |
| hashed_password       |          | can_edit_budget       |
| role (admin/analyst)  |          +-----------------------+
| is_active             |
+-----------------------+
       | 1
       |
       | N
+-----------------------+          +-----------------------+
|      eco_history      | N      1 |         ecos          |
|-----------------------|----------|-----------------------|
| id (PK)               |          | id (PK)               |
| eco_id (FK -> ecos)   |          | codigo_eco (UNIQUE)   |
| user_id (FK -> users) |          | titulo_alteracao      |
| campo_alterado        |          | area_solicitante      |
| valor_anterior        |          | nome_engenheiro_resp  |
| valor_novo            |          | email_solicitante     |
| data_modificacao      |          | data_recebimento      |
+-----------------------+          | nivel_prioridade      |
                                   | status_atual          |
                                   | justificativa_tecnica |
+-----------------------+          | codigo_item_afetado   |
|    field_permissions  |          | categoria_mudanca     |
|-----------------------|          | impacto_custos        |
| id (PK)               |          | estimativa_orcamento  |
| role (admin/analyst)  |          | unidade_fabril        |
| field_name            |          | data_implementacao    |
| is_editable           |          +-----------------------+
+-----------------------+

+-----------------------+          +-----------------------+
|    obu_au_mappings    |          |  owner_group_mappings |
|-----------------------|          |-----------------------|
| id (PK)               |          | id (PK)               |
| obu_code              |          | owner_title           |
| au_code               |          | engineering_group     |
| plant_name            |          | queue_name            |
+-----------------------+          +-----------------------+
```

---

## 2. Catálogo de Entidades Principais

### 2.1. Tabela `users`
Armazena as contas de acesso e credenciais dos operadores e administradores do sistema.
* `id` (SERIAL, PK): Identificador único.
* `username` (VARCHAR(50), UNIQUE, NOT NULL): Nome de usuário para login.
* `email` (VARCHAR(100), UNIQUE, NOT NULL): E-mail do solicitante/operador.
* `hashed_password` (VARCHAR(255), NOT NULL): Hash seguro da senha gerado com bcrypt.
* `role` (VARCHAR(20), NOT NULL): Perfil de acesso (`admin` ou `analyst`).
* `is_active` (BOOLEAN, DEFAULT TRUE): Flag de controle de acesso ativo.

### 2.2. Tabela `ecos`
Representa as Ordens de Mudança de Engenharia e mapeia rigorosamente os 15 campos de controle mestre.
* `id` (SERIAL, PK): Chave primária artificial.
* `codigo_eco` (VARCHAR(50), UNIQUE, NOT NULL): Identificador oficial (ex.: `ECO-00125`).
* `titulo_alteracao` (VARCHAR(255), NOT NULL): Título descritivo da mudança.
* `area_solicitante` (VARCHAR(100), NOT NULL): Departamento de origem.
* `nome_engenheiro_responsavel` (VARCHAR(100), NOT NULL): Responsável técnico.
* `email_solicitante` (VARCHAR(100), NOT NULL): E-mail de contato.
* `data_recebimento` (TIMESTAMP WITH TIME ZONE, NOT NULL): Momento de entrada.
* `nivel_prioridade` (VARCHAR(20), NOT NULL): `BAIXA`, `MEDIA` ou `ALTA`.
* `status_atual` (VARCHAR(50), NOT NULL): Estado no fluxo (`PROCESSADO_SUCESSO`, `PENDENTE_VALIDACAO_HUMANA`, `REJEITADO_DADO_INVALIDO`).
* `justificativa_tecnica` (TEXT, NOT NULL): Justificativa da alteração.
* `codigo_item_afetado` (VARCHAR(100), NOT NULL): Part Number ou código do componente.
* `categoria_mudanca` (VARCHAR(50), NOT NULL): Homologadas: `DisplayMedia`, `Canal de PC` ou `Módulos`.
* `impacto_custos` (VARCHAR(20), NOT NULL): Faixa de impacto financeiro.
* `estimativa_orcamento` (NUMERIC(12, 2), NOT NULL): Valor em USD (com constraint de valor >= 0).
* `unidade_fabril` (VARCHAR(50), NOT NULL): Unidade fabril de destino (padrão: `Manaus`).
* `data_implementacao_alvo` (DATE, NULLABLE): Data prevista de conclusão.

### 2.3. Tabela `eco_history`
Trilha de auditoria das modificações sofridas pelos campos da ECO.
* `id` (SERIAL, PK): Chave primária.
* `eco_id` (INT, FK -> `ecos.id`, NOT NULL): ECO modificada.
* `user_id` (INT, FK -> `users.id`, NOT NULL): Usuário autor da alteração.
* `campo_alterado` (VARCHAR(50), NOT NULL): Nome da coluna modificada.
* `valor_anterior` (TEXT): Valor antigo.
* `valor_novo` (TEXT): Novo valor aplicado.
* `data_modificacao` (TIMESTAMP WITH TIME ZONE, DEFAULT NOW()): Carimbo temporal da ação.

### 2.4. Tabela `analyst_permissions`
Configuração de ações complementares permitidas por analista.
* `id` (SERIAL, PK): Chave primária.
* `user_id` (INT, FK -> `users.id`, NOT NULL): Usuário vinculado.
* `can_approve_exception` (BOOLEAN, DEFAULT FALSE): Se pode liberar desvios operacionais.
* `can_edit_budget` (BOOLEAN, DEFAULT FALSE): Se possui exceção para ajuste de custos.

### 2.5. Tabela `field_permissions`
Matriz de segurança que define quais campos cada perfil (`role`) pode manipular via API.
* `id` (SERIAL, PK): Chave primária.
* `role` (VARCHAR(20), NOT NULL): Perfil avaliado (`admin` ou `analyst`).
* `field_name` (VARCHAR(50), NOT NULL): Nome do campo da ECO.
* `is_editable` (BOOLEAN, NOT NULL): Flag indicando se a edição é autorizada.

### 2.6. Tabela `obu_au_mappings`
Tabela de conversão da Unidade de Negócio de Origem para a Unidade de Aplicação Fabril.
* `id` (SERIAL, PK): Chave primária.
* `obu_code` (VARCHAR(50), NOT NULL): Código da OBU recebido da matriz.
* `au_code` (VARCHAR(50), NOT NULL): Código da AU equivalente.
* `plant_name` (VARCHAR(50), NOT NULL): Planta industrial de destino.

### 2.7. Tabela `owner_group_mappings`
Roteamento do responsável técnico para o grupo de engenharia competente.
* `id` (SERIAL, PK): Chave primária.
* `owner_title` (VARCHAR(100), NOT NULL): Função ou área do responsável técnico.
* `engineering_group` (VARCHAR(100), NOT NULL): Grupo técnico atribuído.
* `queue_name` (VARCHAR(100), NOT NULL): Fila do workflow.

---

## 3. Gestão de Migrações com Alembic

O histórico e evolução do esquema do banco de dados são mantidos de forma programática através do **Alembic**:
* **Gerar nova migração:**
  ```bash
  alembic revision --autogenerate -m "criar_tabelas_iniciais_eco_control"
  ```
* **Aplicar migrações ao banco:**
  ```bash
  alembic upgrade head
  ```
* **Reverter última migração:**
  ```bash
  alembic downgrade -1
  ```

---

## 4. Carga Inicial de Dados (*Seed*)

Para inicializar a base em ambientes de desenvolvimento e homologação, é executado o script `scripts/seed.py`, responsável por:
1. Criar o usuário administrador padrão (`admin` / `admin2026`) com hash seguro.
2. Criar o usuário analista de testes (`aluno` / `avaliacao2026`).
3. Preencher os registros de mapeamento `obu_au_mappings` e `owner_group_mappings`.
4. Inserir a matriz de permissões de campos na tabela `field_permissions`.