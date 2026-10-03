# Regras de Negócio das ECOs — ECO CONTROL

Este documento descreve as principais regras atualmente implementadas no módulo de ECOs do **ECO CONTROL**.

As regras foram extraídas da implementação disponível na branch `develop` e devem ser mantidas alinhadas ao comportamento efetivo do backend.

---

## 1. Origem dos Dados

O ECO CONTROL utiliza como referência a estrutura da planilha:

```text
CTRL GERAL
```

Os dados persistidos são organizados nos seguintes grupos:

```text
IDENTIFICAÇÃO
CLASSIFICAÇÃO
ECO HQ
ORIGEM
AZ ECO
AGREEMENT OTHER DEPTS
R&D APPROVAL
RELEASE
ADICIONAIS
SET ECO
```

Alguns campos presentes na visualização e na exportação são persistidos no banco.

Outros são calculados dinamicamente pelo backend.

---

# 2. Identificação da ECO

Cada registro possui:

```text
id
```

no formato UUID.

Além disso, são utilizados:

```text
item
position
month
```

para organização dos registros.

---

# 3. ITEM

`ITEM` representa a sequência lógica das ECOs.

Ele possui valor único.

Exemplo:

```text
ITEM 1
ITEM 2
ITEM 3
ITEM 4
```

A criação e exclusão de registros podem provocar reorganização dessa sequência.

---

# 4. POSITION

`POSITION` é utilizado para auxiliar na ordenação dos registros.

O sistema mantém ITEM e POSITION sincronizados conforme as operações de inserção e exclusão.

---

# 5. Ordenação da Listagem

A listagem principal utiliza:

```text
ITEM DESC
POSITION DESC
```

Portanto, registros com ITEM maior aparecem primeiro.

---

# 6. Criação Normal de ECO

A criação padrão ocorre através de:

```text
POST /api/v1/ecos
```

Antes de criar, o backend valida:

```text
usuário pode criar?
```

Administradores podem criar.

Analistas precisam possuir:

```text
can_create_eco = true
```

Além disso, para analistas, os campos enviados precisam possuir:

```text
can_edit = true
```

---

# 7. Valores Gerados na Criação

Na criação normal, o backend gera automaticamente:

```text
ITEM
POSITION
MONTH
```

O mês é determinado a partir da data atual.

Exemplo:

```text
JAN
FEB
MAR
APR
MAY
JUN
JUL
AUG
SEP
OCT
NOV
DEC
```

---

# 8. Regra OBU → AU

Quando uma ECO possui:

```text
obu
```

o backend consulta:

```text
obu_au_mappings
```

Fluxo:

```text
OBU
 ↓
SettingsRepository
 ↓
obu_au_mappings
 ↓
AU
```

Exemplo conceitual:

```text
NWE
 ↓
GLZ
```

O valor de AU não deve ser mantido como uma regra fixa espalhada no código.

A relação pode ser administrada através das configurações.

---

# 9. Atualização de OBU

Durante uma atualização:

```text
PATCH /api/v1/ecos/{eco_id}
```

se `obu` for alterado, o backend recalcula:

```text
au
```

com base no mapeamento cadastrado.

---

# 10. Regra OWNER → GROUP

O backend também possui um mapeamento entre:

```text
OWNER
 ↓
GROUP
```

armazenado em:

```text
owner_group_mappings
```

Quando uma ECO possui OWNER e nenhum GROUP explícito é informado, o sistema pode preencher automaticamente o GROUP correspondente.

---

# 11. Atualização de OWNER

Se uma atualização contém:

```text
owner
```

e não contém um GROUP informado explicitamente, o backend consulta o mapeamento:

```text
OWNER → GROUP
```

e atualiza:

```text
group_name
```

automaticamente.

Externamente, a API utiliza:

```text
group
```

Internamente, o banco utiliza:

```text
group_name
```

---

# 12. Criação abaixo de outra ECO

O endpoint:

```text
POST /api/v1/ecos/{eco_id}/after
```

permite criar uma nova ECO imediatamente abaixo da ECO selecionada.

Exemplo:

```text
Antes:

ITEM 7
ITEM 8
ITEM 9
```

Criando abaixo do ITEM 7:

```text
ITEM 7
ITEM 8  ← nova ECO
ITEM 9  ← antiga ITEM 8
ITEM 10 ← antiga ITEM 9
```

O backend ajusta automaticamente:

```text
ITEM
POSITION
```

das ECOs afetadas.

---

# 13. Atualização de ECO

A atualização utiliza:

```text
PATCH /api/v1/ecos/{eco_id}
```

Somente os campos enviados são processados.

Exemplo:

```json
{
  "owner": "kamila.pimentel",
  "status": "RELEASED",
  "comments": "ECO atualizada"
}
```

Fluxo:

```text
Payload
   ↓
exclude_unset
   ↓
normalização
   ↓
permissões
   ↓
regras automáticas
   ↓
comparação valor anterior / novo
   ↓
persistência
   ↓
histórico
```

Campos que não sofreram alteração efetiva não precisam gerar mudança.

---

# 14. Normalização de Texto

Valores textuais recebidos são normalizados antes da persistência.

Atualmente a função:

```text
normalize_text()
```

remove espaços nas extremidades das strings.

Exemplo:

```text
"  RELEASED  "
```

torna-se:

```text
"RELEASED"
```

---

# 15. Exclusão Individual

O endpoint:

```text
DELETE /api/v1/ecos/{eco_id}
```

é restrito a administradores.

Fluxo:

```text
buscar ECO
 ↓
registrar histórico
 ↓
excluir
 ↓
reorganizar ITEM
 ↓
reorganizar POSITION
 ↓
commit
```

---

# 16. Exclusão Múltipla

O endpoint:

```text
POST /api/v1/ecos/bulk-delete
```

permite excluir várias ECOs selecionadas.

Essa operação também é restrita a:

```text
admin
```

O backend:

1. remove IDs duplicados da requisição;
2. valida se todas as ECOs existem;
3. registra o histórico;
4. exclui somente as ECOs selecionadas;
5. reorganiza ITEM;
6. reorganiza POSITION;
7. confirma a transação.

Caso qualquer etapa falhe:

```text
rollback
```

é executado.

---

# 17. Limite da Exclusão Múltipla

O schema atual permite:

```text
mínimo: 1 UUID
máximo: 500 UUIDs
```

por requisição.

---

# 18. Histórico

As principais operações sobre ECOs geram registros de auditoria.

Ações utilizadas:

```text
created
updated
deleted
```

Cada alteração pode registrar:

```text
eco_id
eco_code
item
field_key
field_label
old_value
new_value
user_email
user_name
action
created_at
```

---

# 19. Preservação do Histórico

O histórico deve continuar disponível mesmo depois que uma ECO é excluída.

Por isso, o sistema preserva dados como:

```text
eco_code
item
campo
valor anterior
valor novo
usuário
ação
data
```

sem depender da existência posterior do registro na tabela `ecos`.

---

# 20. Campos Persistidos

Entre os campos persistidos estão:

### Identificação

```text
product
obu
au
```

### Classificação

```text
group_name
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

### Agreement

```text
agreement_start_1
agreement_finish_1

agreement_start_2
agreement_finish_2

agreement_start_3
agreement_finish_3
```

### R&D

```text
second_aprov_rd
second_aprov_rd_start_1
second_aprov_rd_finish_1
second_aprov_rd_start_2
second_aprov_rd_finish_2
```

### Adicionais

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

# 21. Campos Calculados

Alguns valores da CTRL GERAL são calculados pelo backend e não precisam existir como colunas persistidas.

A função principal está localizada em:

```text
server/app/utils/eco_calculations.py
```

através de:

```text
compute_eco_fields()
```

Entre os campos calculados estão:

```text
GAP
Delay ECO Register
ECO Registration Week

ECO Origem 1
ECO Origem 2
ECO Origem 3

GAP Start AZ ECO
Contar ECO emitida > 1 dia

GAP Agreement
GAP Agreement 1
GAP Agreement 2
GAP Agreement 3
GAP Total Agreement

GAP 2ST 1
GAP 2ST 2
GAP Total 2ST

ECO Release Week
AZ Gap

Contar ECO 7
Contar ECO 10
Contar ECO 14

Total Gap
Release Month
Release Year
```

A API inclui esses valores na serialização da ECO.

---

# 22. Regra Geral do GAP

O campo GAP considera o status e as datas disponíveis.

Quando a ECO não possui código:

```text
GAP = vazio
```

Quando o status é:

```text
RELEASED
CANCELLED
```

o resultado é:

```text
OK
```

Nos demais casos, quando existe:

```text
AZ ECO REGISTER DATE
```

o backend calcula a diferença de dias até a data de referência.

---

# 23. GAP de Períodos

Para períodos com data inicial e final, o backend utiliza regras de cálculo de diferença em dias.

Quando não existe início:

```text
0
```

pode ser utilizado conforme a regra da planilha.

Quando existe início, mas não existe fim:

```text
None
```

é utilizado para representar um período incompleto.

Assim o sistema evita gerar artificialmente um valor negativo.

---

# 24. Importação XLSX

A importação aceita:

```text
.xlsx
```

e exige a aba:

```text
CTRL GERAL
```

O arquivo possui limite de:

```text
25 MB
```

---

# 25. Preview de Importação

Antes da importação definitiva, o endpoint:

```text
POST /api/v1/ecos/import/preview
```

analisa o arquivo.

Nenhum dado é persistido nessa etapa.

O preview identifica situações como:

```text
NEW
DUPLICATE
ERROR
```

e também pode gerar warnings.

---

# 26. Regra da Importação Definitiva

O endpoint:

```text
POST /api/v1/ecos/import
```

utiliza o resultado das validações.

A regra principal é:

```text
ERROR
 ↓
cancela o lote
```

```text
DUPLICATE
 ↓
não insere novamente
```

```text
NEW
 ↓
persiste
```

A operação é transacional.

Em caso de falha:

```text
rollback
```

é executado.

---

# 27. Permissão de Importação

Administradores possuem acesso.

Analistas precisam possuir:

```text
can_bulk_edit = true
```

Caso contrário:

```text
403 Forbidden
```

é retornado.

---

# 28. Preservação de Textos

Os campos textuais importados da planilha devem preservar o conteúdo completo.

Por isso, diversos campos anteriormente limitados por `VARCHAR` foram convertidos para:

```text
TEXT
```

A regra evita:

```text
truncamento
perda de conteúdo
falha por tamanho excedido
```

principalmente em textos como:

```text
COMMENTS
CHANGE REASON
MODEL
dados técnicos
```

---

# 29. Exportação XLSX

A exportação utiliza:

```text
GET /api/v1/ecos/export
```

e respeita os filtros utilizados na listagem.

Filtros disponíveis incluem:

```text
search
status
month
group
obu
item_type
eco_type
column_filters
```

Fluxo:

```text
Filtros da tela
      ↓
consulta
      ↓
campos calculados
      ↓
arquivo XLSX
```

---

# 30. Permissões por Campo

Analistas podem possuir regras diferentes para cada campo.

Cada permissão define:

```text
can_view
can_edit
```

`can_view = false` impede que o campo seja entregue normalmente ao usuário.

`can_edit = false` impede alterações.

Administradores não dependem dessas permissões individuais.

---

# 31. Regras Administrativas

As seguintes operações são administrativas:

```text
exclusão individual de ECO
exclusão múltipla
gerenciamento de usuários
gerenciamento de permissões
cadastro de OBU → AU
cadastro de OWNER → GROUP
gerenciamento de configurações
```

A API valida:

```text
role == admin
```

antes de permitir essas ações.

---

# 32. Princípio de Centralização das Regras

As regras não devem depender somente do frontend.

O modelo utilizado é:

```text
Angular
 ↓
envia intenção/dados

FastAPI
 ↓
valida
 ↓
aplica permissões
 ↓
aplica regra de negócio
 ↓
registra histórico
 ↓
PostgreSQL
```

O backend permanece como fonte principal das regras operacionais.

---

# 33. Manutenção

Sempre que forem alterados:

- campos da ECO;
- fórmulas;
- regras de importação;
- regras de exclusão;
- ITEM/POSITION;
- mapeamentos;
- permissões;
- histórico;

este documento deve ser atualizado.

A implementação presente em:

```text
server/app/services/
server/app/repository/
server/app/utils/eco_calculations.py
server/app/controller/eco_controller.py
```

é a referência técnica para o comportamento atual.