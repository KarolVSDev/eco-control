# Documentação da API REST — ECO CONTROL

Este documento descreve o contrato atual de integração entre o frontend **Angular** e o backend **FastAPI** do sistema **ECO CONTROL**.

A documentação deve acompanhar a implementação disponível na branch `develop`. Sempre que endpoints, schemas ou regras de negócio forem alterados, este documento também deverá ser atualizado.

---

## 1. Convenções Globais e URL Base

- **URL Base local:** `http://localhost:8000/api/v1`
- **Swagger:** `http://localhost:8000/docs`
- **Health Check:** `http://localhost:8000/health`
- **Formato padrão:** `application/json`
- **Upload de arquivos:** `multipart/form-data`
- **Autenticação:** JWT Bearer Token.

Para as rotas protegidas, o frontend envia:

```http
Authorization: Bearer <access_token>
```

O backend utiliza FastAPI, Pydantic, SQLAlchemy e PostgreSQL.

---

# 2. Autenticação

## `POST /api/v1/auth/login`

Autentica um usuário por e-mail e senha e retorna um token JWT.

### Content-Type

```text
application/json
```

### Corpo da requisição

```json
{
  "email": "admin@eco.com",
  "password": "admin123"
}
```

### Resposta de sucesso — `200 OK`

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "user": {
    "id": "<uuid>",
    "email": "admin@eco.com",
    "full_name": "Administrador Local",
    "role": "admin"
  }
}
```

### Possíveis erros

- `401 Unauthorized`: e-mail ou senha inválidos.

---

## `PATCH /api/v1/auth/change-password`

Permite ao usuário autenticado alterar a própria senha.

### Corpo da requisição

```json
{
  "current_password": "senha_atual",
  "new_password": "nova_senha"
}
```

A nova senha deve possuir no mínimo 6 caracteres.

### Resposta de sucesso — `200 OK`

```json
{
  "message": "Senha alterada com sucesso."
}
```

### Possíveis erros

- `400 Bad Request`: senha atual incorreta;
- `400 Bad Request`: nova senha igual à senha atual;
- `401 Unauthorized`: usuário não autenticado;
- `422 Unprocessable Entity`: payload inválido.

---

## `GET /api/v1/auth/permissions`

Retorna as permissões do usuário autenticado.

### Resposta de administrador

Administradores possuem acesso total às permissões gerais.

```json
{
  "role": "admin",
  "general": {
    "can_create_eco": true,
    "can_bulk_edit": true,
    "can_view_history": true
  },
  "fields": []
}
```

### Resposta de analista

```json
{
  "role": "analyst",
  "general": {
    "can_create_eco": true,
    "can_bulk_edit": false,
    "can_view_history": true
  },
  "fields": [
    {
      "field_key": "owner",
      "can_view": true,
      "can_edit": true
    }
  ]
}
```

As permissões específicas dos analistas são configuradas individualmente.

---

# 3. ECO Control

## `GET /api/v1/ecos`

Retorna a listagem paginada das ECOs utilizadas na tela principal do ECO CONTROL.

### Parâmetros de consulta

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `page` | inteiro | Página solicitada. Padrão: `1` |
| `page_size` | inteiro | Registros por página. Padrão: `50`. Máximo: `500` |
| `search` | string | Pesquisa geral |
| `status` | string | Filtro por STATUS |
| `month` | string | Filtro por MONTH |
| `group` | string | Filtro por GROUP |
| `obu` | string | Filtro por OBU |
| `item_type` | string | Filtro por ITEM TYPE |
| `eco_type` | string | Filtro por ECO TYPE |
| `column_filters` | string JSON | Filtros específicos por coluna |

### Resposta

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 50
}
```

Os registros são apresentados utilizando **ITEM em ordem decrescente**.

A resposta também pode conter campos calculados pelo backend.

---

## Estrutura principal de uma ECO

Os dados persistidos seguem a estrutura da planilha `CTRL GERAL`.

Entre os principais campos estão:

### Identificação

```text
product
obu
au
group
owner
item_type
eco_type
change_bom
status
receb
```

### ECO HQ

```text
eco
change_reason
hq_eco_release_date
az_eco_register_date
auto_ecr
council_meeting_week
```

### Origem

```text
hz_in_kr_eco_1
hz_sh_in_receive_date_1

hz_in_kr_eco_2
hz_sh_in_receive_date_2

hz_in_kr_eco_3
hz_sh_in_receive_date_3
```

### AZ ECO

```text
az_eco_no
change_reason2
change_bom_az
az_eco_creation_date
```

### Agreement Other Departments

```text
agreement_start_1
agreement_finish_1

agreement_start_2
agreement_finish_2

agreement_start_3
agreement_finish_3
```

### R&D Approval

```text
second_aprov_rd
second_aprov_rd_start_1
second_aprov_rd_finish_1
second_aprov_rd_start_2
second_aprov_rd_finish_2
```

### Campos adicionais

```text
change_reason_az
model_az
new_model
origem_approval
event
comments
```

### SET ECO

```text
set_eco
set_eco_register_date
set_eco_release_date
set_eco_change_reason
set_eco_model
```

---

# 4. Criação de ECO

## `POST /api/v1/ecos`

Cria uma nova ECO.

Administradores possuem permissão automaticamente.

Analistas precisam possuir:

```text
can_create_eco = true
```

Além disso, os campos enviados por analistas continuam sujeitos às respectivas permissões `can_edit`.

### Exemplo de requisição

```json
{
  "product": "Produto exemplo",
  "obu": "NWE",
  "owner": "kamila.pimentel",
  "item_type": "MEC",
  "eco_type": "REGULAR",
  "change_bom": "YES",
  "status": "WORKING",
  "eco": "EKLP123456",
  "change_reason": "Alteração de engenharia",
  "comments": "Registro criado pelo ECO CONTROL"
}
```

O backend pode preencher ou calcular automaticamente:

- `ITEM`;
- `POSITION`;
- `MONTH`;
- `AU`, conforme o mapeamento OBU → AU;
- `GROUP`, conforme o mapeamento OWNER → GROUP.

### Possíveis erros

- `403 Forbidden`: usuário sem permissão de criação ou edição do campo;
- `422 Unprocessable Entity`: payload inválido.

---

# 5. Criar ECO abaixo de outra ECO

## `POST /api/v1/ecos/{eco_id}/after`

Cria uma nova ECO imediatamente abaixo da ECO informada.

### Parâmetro de rota

```text
eco_id = UUID da ECO de referência
```

O backend reorganiza automaticamente:

- `ITEM`;
- `POSITION`.

Exemplo conceitual:

```text
Antes:

ITEM 7
ITEM 8
ITEM 9

Criando abaixo do ITEM 7:

ITEM 7
ITEM 8  ← nova ECO
ITEM 9  ← antiga ITEM 8
ITEM 10 ← antiga ITEM 9
```

### Possíveis erros

- `403 Forbidden`: sem permissão para criar ECOs;
- `404 Not Found`: ECO de referência inexistente;
- `409 Conflict`: ECO de referência sem ITEM/POSITION válido.

---

# 6. Atualização de ECO

## `PATCH /api/v1/ecos/{eco_id}`

Atualiza somente os campos enviados na requisição.

### Parâmetro

```text
eco_id = UUID
```

### Exemplo

```json
{
  "owner": "kamila.pimentel",
  "status": "RELEASED",
  "comments": "ECO revisada"
}
```

### Regras automáticas

Quando `obu` é alterado:

```text
OBU
 ↓
mapeamento OBU → AU
 ↓
AU atualizada
```

Quando `owner` é alterado e nenhum `group` é enviado explicitamente:

```text
OWNER
  ↓
mapeamento OWNER → GROUP
  ↓
GROUP atualizada
```

Toda alteração efetivamente realizada é registrada no histórico.

### Permissões

- `admin`: pode editar os campos permitidos pelo schema;
- `analyst`: somente campos configurados com `can_edit = true`.

### Possíveis erros

- `403 Forbidden`: usuário sem permissão para editar um ou mais campos;
- `404 Not Found`: ECO inexistente;
- `422 Unprocessable Entity`: payload inválido.

---

# 7. Exclusão individual

## `DELETE /api/v1/ecos/{eco_id}`

Exclui uma ECO.

### Acesso

**Somente administradores.**

### Comportamento

Depois da exclusão, o backend reorganiza:

- `ITEM`;
- `POSITION`.

A exclusão também é registrada no histórico.

### Resposta

```text
204 No Content
```

### Possíveis erros

- `403 Forbidden`: usuário não é administrador;
- `404 Not Found`: ECO não encontrada.

---

# 8. Exclusão múltipla

## `POST /api/v1/ecos/bulk-delete`

Exclui somente as ECOs selecionadas pelo administrador.

### Acesso

**Somente administradores.**

### Corpo da requisição

```json
{
  "ids": [
    "uuid-eco-1",
    "uuid-eco-2",
    "uuid-eco-3"
  ]
}
```

São aceitos de **1 a 500 UUIDs** por requisição.

### Resposta

```json
{
  "deleted_rows": 3
}
```

### Comportamento

O processo:

1. valida os UUIDs;
2. verifica se todas as ECOs existem;
3. registra o histórico das exclusões;
4. remove somente as ECOs selecionadas;
5. reorganiza ITEM;
6. reorganiza POSITION;
7. realiza commit da transação.

### Possíveis erros

- `403 Forbidden`: operação realizada por usuário não administrador;
- `404 Not Found`: uma ou mais ECOs não encontradas;
- `422 Unprocessable Entity`: lista de IDs inválida.

---

# 9. Preview da Importação XLSX

## `POST /api/v1/ecos/import/preview`

Analisa uma planilha antes da importação definitiva.

**Nenhuma alteração é persistida durante o preview.**

### Content-Type

```text
multipart/form-data
```

### Campo

```text
file
```

### Regras do arquivo

- somente arquivos `.xlsx`;
- tamanho máximo de **25 MB**;
- deve existir uma aba chamada `CTRL GERAL`.

### Permissão

A operação é permitida para:

- `admin`;
- analista com `can_bulk_edit = true`.

### O preview identifica

- total de linhas;
- linhas válidas;
- novas ECOs;
- duplicadas;
- erros;
- warnings;
- valores derivados;
- campos calculados ignorados durante a leitura.

Exemplo conceitual:

```json
{
  "file_name": "CONTROLE_ECO_2026.xlsx",
  "sheet": "CTRL GERAL",
  "total_rows": 100,
  "new_rows": 20,
  "duplicate_rows": 75,
  "error_rows": 5,
  "warning_rows": 2,
  "can_import": false,
  "rows": []
}
```

### Classificação das linhas

Uma linha pode possuir ação:

```text
NEW
DUPLICATE
ERROR
```

Warnings podem existir sem impedir necessariamente a importação.

### Importante

O preview:

- não cria ECO;
- não atualiza ECO;
- não realiza commit no banco.

---

# 10. Importação XLSX

## `POST /api/v1/ecos/import`

Executa a importação definitiva.

### Content-Type

```text
multipart/form-data
```

### Campo

```text
file
```

### Permissão

- `admin`;
- analista com `can_bulk_edit = true`.

### Regras

A operação é transacional.

```text
ERROR
 ↓
cancela o lote

DUPLICATE
 ↓
ignorada

NEW
 ↓
persistida
```

Somente linhas classificadas como `NEW` são inseridas.

Se ocorrer qualquer falha durante a gravação:

```text
rollback
```

é executado e o lote não é parcialmente confirmado.

### Possíveis erros

- `403 Forbidden`: sem permissão de importação;
- `409 Conflict`: nenhuma linha nova encontrada;
- `413 Payload Too Large`: arquivo maior que 25 MB;
- `422 Unprocessable Entity`: arquivo inválido ou existência de erros no lote.

---

# 11. Campos calculados

Diversos campos da `CTRL GERAL` são calculados pelo backend e não são importados diretamente como valores confiáveis da planilha.

Entre eles estão:

```text
GAP
1-Delay ECO Register
ECO registration week
ECO Origem (1)
ECO Origem (2)
ECO Origem (3)
GAP Start AZ ECO
Contar Eco emitida > 1 dias
GAP AGREEMENT
GAP AGREEMENT OTHER DEPTS
GAP TOTAL AGREEMENT OTHER DEPTS
GAP 2ST APROV R&D
GAP TOTAL 2ST APROV R&D
ECO release week
AZ Gap
Contar Eco concluída > 7 dias
Contar Eco concluída > 10 dias
Total Gap
RELEASE MONTH
RELEASE YEAR
```

As regras de cálculo ficam centralizadas no backend.

---

# 12. Exportação XLSX

## `GET /api/v1/ecos/export`

Gera um arquivo `.xlsx` no formato da `CTRL GERAL`.

### Filtros disponíveis

- `search`;
- `status`;
- `month`;
- `group`;
- `obu`;
- `item_type`;
- `eco_type`;
- `column_filters`.

A exportação utiliza os mesmos filtros aplicados à listagem do ECO Control.

Isso permite, por exemplo:

```text
Aplicar filtros na tela
       ↓
Exportar
       ↓
Excel contendo somente os dados filtrados
```

### Nome do arquivo

O formato utilizado é:

```text
ECO_CONTROL_YYYY-MM-DD.xlsx
```

---

# 13. Dashboard

## `GET /api/v1/dashboard/stats`

Retorna os indicadores principais.

Entre os indicadores utilizados atualmente estão:

- total;
- working;
- on hold;
- processing;
- released;
- rejected;
- cancelled;
- overdue;
- GAP > 7;
- GAP > 14.

---

## `GET /api/v1/dashboard/months`

Retorna os meses disponíveis na base de ECOs.

---

## `GET /api/v1/dashboard/group/{dimension}`

Agrupa as ECOs por uma dimensão.

### Dimensões permitidas

```text
status
group
owner
obu
au
eco_type
```

É possível utilizar `month` como filtro opcional.

---

## `GET /api/v1/dashboard/evolution`

Retorna a evolução das ECOs por mês.

---

## `GET /api/v1/dashboard/delay`

Retorna informações relacionadas aos indicadores de atraso.

Aceita `month` como filtro opcional.

---

## `GET /api/v1/dashboard/monthly-summary`

Retorna o resumo mensal utilizado no dashboard.

---

# 14. Histórico e Auditoria

## `GET /api/v1/history`

Retorna o histórico de criação, alteração e exclusão das ECOs.

### Filtros

| Parâmetro | Descrição |
|---|---|
| `page` | Página |
| `page_size` | Registros por página |
| `date_start` | Data inicial |
| `date_end` | Data final |
| `user_email` | Usuário |
| `field` | Campo |
| `action` | Tipo da ação |
| `eco` | Código da ECO |
| `search` | Busca geral |

### Ações permitidas

```text
created
updated
deleted
```

### Permissão

O administrador pode visualizar o histórico.

Um analista precisa possuir:

```text
can_view_history = true
```

Além disso, o backend respeita campos configurados com `can_view = false`, evitando exposição indevida de informações no histórico.

### Estrutura conceitual

```json
{
  "items": [
    {
      "id": "<uuid>",
      "eco_id": "<uuid>",
      "eco_code": "EKLP123456",
      "item": 10,
      "field_key": "status",
      "field_label": "STATUS",
      "old_value": "WORKING",
      "new_value": "RELEASED",
      "user_email": "usuario@empresa.com",
      "user_name": "Usuário",
      "action": "updated",
      "created_at": "2026-10-02T14:30:00"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

---

## `GET /api/v1/history/export`

Exporta o histórico utilizando os mesmos filtros disponíveis na listagem.

### Formato

```text
CSV UTF-8
```

O arquivo é gerado como:

```text
historico-eco-control.csv
```

O backend também protege valores contra interpretação indevida como fórmulas pelo Excel.

---

# 15. Usuários — Administração

As rotas desta seção exigem perfil:

```text
admin
```

## `GET /api/v1/users`

Lista os usuários cadastrados.

---

## `POST /api/v1/users`

Cria um novo usuário.

### Corpo

```json
{
  "full_name": "Nome do usuário",
  "email": "usuario@empresa.com",
  "password": "senha123",
  "role": "analyst",
  "active": true
}
```

Os papéis aceitos são:

```text
admin
analyst
```

### Resposta

```text
201 Created
```

---

## `PATCH /api/v1/users/{user_id}/password`

Permite ao administrador redefinir a senha de outro usuário.

### Corpo

```json
{
  "new_password": "nova_senha"
}
```

---

## `DELETE /api/v1/users/{user_id}`

Exclui um usuário.

### Resposta

```text
204 No Content
```

---

# 16. Administração de Permissões

## `GET /api/v1/permissions`

Retorna as permissões gerais e por campo configuradas para os analistas.

Acesso restrito a administradores.

---

## `GET /api/v1/permissions/{user_email}`

Retorna as permissões específicas de um analista.

Exemplo:

```json
{
  "user": {
    "id": "<uuid>",
    "email": "analista@empresa.com",
    "full_name": "Analista"
  },
  "general": {
    "can_create_eco": true,
    "can_bulk_edit": true,
    "can_view_history": true
  },
  "fields": [
    {
      "field_key": "owner",
      "can_view": true,
      "can_edit": true
    }
  ]
}
```

---

## `PUT /api/v1/permissions/{user_email}`

Atualiza as permissões de um analista.

### Exemplo

```json
{
  "general": {
    "can_create_eco": true,
    "can_bulk_edit": false,
    "can_view_history": true
  },
  "fields": [
    {
      "field_key": "owner",
      "can_view": true,
      "can_edit": true
    },
    {
      "field_key": "comments",
      "can_view": true,
      "can_edit": false
    }
  ]
}
```

Permissões específicas somente podem ser configuradas para usuários com perfil `analyst`.

---

# 17. Configurações

## `GET /api/v1/settings`

Retorna as configurações administrativas.

Acesso restrito a administradores.

A resposta contempla:

- relações OBU → AU;
- relações OWNER → GROUP;
- gerentes cadastrados.

---

## `GET /api/v1/settings/owner-options`

Retorna as opções de OWNER e seus respectivos GROUPs.

A rota exige usuário autenticado.

Exemplo:

```json
[
  {
    "owner": "kamila.pimentel",
    "group": "BOM"
  }
]
```

---

# 18. Mapeamento OBU → AU

## `POST /api/v1/settings/obu-au`

Cria uma relação OBU → AU.

Acesso restrito a administradores.

### Exemplo

```json
{
  "obu": "NWE",
  "au": "GLZ"
}
```

A OBU é armazenada em maiúsculas.

Não é permitido cadastrar duas relações para a mesma OBU.

---

## `PUT /api/v1/settings/obu-au/{mapping_id}`

Atualiza uma relação OBU → AU.

### Parâmetro

```text
mapping_id = UUID
```

---

## `DELETE /api/v1/settings/obu-au/{mapping_id}`

Remove uma relação.

### Resposta

```text
204 No Content
```

---

# 19. Mapeamento OWNER → GROUP

## `POST /api/v1/settings/owner-group`

Cria uma relação OWNER → GROUP.

### Exemplo

```json
{
  "owner": "kamila.pimentel",
  "group": "BOM"
}
```

Acesso restrito a administradores.

---

## `DELETE /api/v1/settings/owner-group/{mapping_id}`

Remove uma relação OWNER → GROUP.

### Resposta

```text
204 No Content
```

---

# 20. Gerentes

## `POST /api/v1/settings/managers`

Adiciona um gerente às configurações do ECO CONTROL.

### Exemplo

```json
{
  "name": "Nome do gerente"
}
```

Acesso restrito a administradores.

---

## `DELETE /api/v1/settings/managers/{manager_id}`

Remove um gerente.

### Resposta

```text
204 No Content
```

---

# 21. Códigos HTTP utilizados

| Código | Significado | Uso |
|---|---|---|
| `200 OK` | Sucesso | Consulta, alteração ou operação realizada |
| `201 Created` | Criado | Recurso criado |
| `204 No Content` | Sucesso sem corpo | Exclusões |
| `400 Bad Request` | Requisição inválida | Regra ou parâmetro inválido |
| `401 Unauthorized` | Não autenticado | Token ausente, inválido ou expirado |
| `403 Forbidden` | Acesso negado | Usuário sem permissão |
| `404 Not Found` | Não encontrado | Registro inexistente |
| `409 Conflict` | Conflito | Estado incompatível ou recurso duplicado |
| `413 Payload Too Large` | Arquivo muito grande | Upload superior ao limite de 25 MB |
| `422 Unprocessable Entity` | Erro de validação | Payload, arquivo ou parâmetros inválidos |
| `500 Internal Server Error` | Erro interno | Falha inesperada no processamento |

---

# 22. Segurança e Permissões

As regras de autorização são aplicadas no backend.

O frontend pode ocultar ou desabilitar recursos conforme as permissões do usuário, porém o backend continua sendo responsável pela validação definitiva.

O ECO CONTROL utiliza:

```text
JWT
+
perfil do usuário
+
permissões gerais
+
permissões por campo
```

Administradores possuem acesso administrativo total.

Analistas possuem permissões configuráveis individualmente.

---

# 23. Auditoria

Operações relevantes sobre ECOs geram registros no histórico.

As ações atualmente registradas incluem:

```text
created
updated
deleted
```

São armazenadas informações como:

- ECO;
- ITEM;
- usuário;
- e-mail;
- campo alterado;
- valor anterior;
- valor novo;
- ação;
- data e hora.

O histórico foi estruturado para continuar disponível mesmo quando a ECO original for excluída.

---

# 24. Observações de manutenção

Esta documentação descreve a API disponível na implementação atual do ECO CONTROL.

Ao modificar:

- controllers;
- schemas;
- permissões;
- importação;
- exportação;
- campos da ECO;
- endpoints;
- regras de negócio;

a documentação correspondente em `docs/` também deve ser atualizada.

A especificação interativa disponível no Swagger continua sendo a principal referência técnica automática das rotas expostas pelo FastAPI:

```text
http://localhost:8000/docs
```