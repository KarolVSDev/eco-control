# Integração da automação de ECOs com o ECO CONTROL
Referência técnica do contrato atual, conferida no código em 28/10/2026.

## Índice

- [Visão geral e endereço](#visão-geral-e-endereço)
- [Autenticação](#autenticação)
- [Contrato do payload](#contrato-do-payload)
- [Valores omitidos, nulos e vazios](#valores-omitidos-nulos-e-vazios)
- [Campos fixos GROUP e OWNER](#campos-fixos-group-e-owner)
- [Matching e persistência](#matching-e-persistência)
- [Respostas e idempotência](#respostas-e-idempotência)
- [Status HTTP e erros](#status-http-e-erros)
- [Conta técnica da automação](#conta-técnica-da-automação)
- [Auditoria](#auditoria)
- [Exemplos de chamadas](#exemplos-de-chamadas)
- [Interface e segurança](#interface-e-segurança)
- [Pendências funcionais](#pendências-funcionais)
- [Fontes da implementação](#fontes-da-implementação)
- [Fluxograma final](#fluxograma-final)

## Visão geral e endereço

A integração faz um **upsert controlado**, processando uma ECO por requisição:

```text
Automação coleta os dados da ECO
        ↓
autentica no ECO CONTROL e obtém JWT
        ↓
POST /api/v1/integrations/eco-automation
        ↓
busca pelo código ECO completo
        ↓
0 registros → cria
1 registro  → atualiza ou mantém
2+ registros → 409 Conflict
```

Endpoint relativo:

```http
POST /api/v1/integrations/eco-automation
Content-Type: application/json
Authorization: Bearer <access_token>
```

A URL real deve vir da configuração ou de variável de ambiente da automação.
Por exemplo, `ECO_CONTROL_API_BASE_URL` pode representar a base já incluindo
`/api/v1`; nesse caso, acrescente somente `/integrations/eco-automation`.
Esse nome de variável é uma sugestão para o cliente, não uma configuração
implementada pelo servidor.

Exemplo exclusivamente de desenvolvimento: `http://127.0.0.1:8001/api/v1`.
Não representa o endereço de produção.

## Autenticação

O login real é `POST /api/v1/auth/login`. O corpo é JSON, não formulário OAuth:

```http
POST /api/v1/auth/login
Content-Type: application/json
```

```json
{
  "email": "conta.tecnica@example.com",
  "password": "<senha obtida de secret ou variável de ambiente>"
}
```

Os valores acima são placeholders; nenhuma conta ou senha é fornecida por este
documento. `email` é validado como endereço de e-mail.

Resposta de sucesso, HTTP 200:

```json
{
  "access_token": "<JWT retornado pelo login>",
  "token_type": "bearer",
  "user": {
    "id": "11111111-1111-4111-8111-111111111111",
    "email": "conta.tecnica@example.com",
    "full_name": "Conta técnica",
    "role": "analyst"
  }
}
```

Fluxo: login → `access_token` → header `Authorization: Bearer ...` → integração.
O JWT possui expiração definida pela configuração do servidor. O endpoint
verifica o token e consulta o usuário; o usuário precisa existir e estar ativo.
Token inválido/expirado resulta em 401. Na implementação atual, a ausência do
Bearer ou um esquema de autenticação incompatível é rejeitado com **403** pelo
`HTTPBearer`, antes da validação do token. Não pressupor que todo erro de
autenticação será 401.

## Contrato do payload

Somente os nove campos abaixo são aceitos. O schema usa `extra="forbid"`:
qualquer outro campo provoca HTTP 422.

| Campo API | Origem na automação | Obrigatório | Tipo aceito |
|---|---|---:|---|
| `eco` | `Common ECO No` | Sim | string não vazia após trim |
| `obu` | `Org Code` | Não | string ou null |
| `change_reason` | `Change Reason` | Não | string ou null |
| `eco_type` | `ECO Type` | Não | string ou null |
| `az_eco_register_date` | `AZ ECO REGISTER DATE` | Não | date ou null |
| `hq_eco_release_date` | `Approved Date` | Não | date ou null |
| `auto_ecr` | `Auto ECR?` | Não | string `YES` / `NO` ou null |
| `change_bom` | `Change BOM?` | Não | string `YES` / `NO` ou null |
| `title` | `Title` | Não | string ou null |

Schema implementado, em notação Python:

```python
eco: str  # min_length=1, após normalização
obu: str | None = None
change_reason: str | None = None
eco_type: str | None = None
az_eco_register_date: date | None = None
hq_eco_release_date: date | None = None
auto_ecr: Literal["YES", "NO"] | None = None
change_bom: Literal["YES", "NO"] | None = None
title: str | None = None
```

Exemplo de payload:

```json
{
  "eco": "ECO123",
  "obu": "NW1",
  "change_reason": "BOM Sync.",
  "eco_type": "REGULAR",
  "az_eco_register_date": "2026-10-27",
  "hq_eco_release_date": "2026-10-28",
  "auto_ecr": "YES",
  "change_bom": "NO",
  "title": "Alteração de componente"
}
```

### Datas

Envie `az_eco_register_date` e `hq_eco_release_date` como strings JSON no formato `YYYY-MM-DD`, por
exemplo `"2026-10-27"`. O campo é tipado como `date` pelo Pydantic; datas
inválidas, como `"2026-02-30"`, resultam em 422. A integração não faz conversão
manual de formatos de planilha. O schema não declara modo estrito adicional
ao tipo `date`; o cliente deve utilizar o formato ISO indicado.
O formato `DD/MM/YYYY` não é aceito e retorna 422 para ambos os campos.

Mapeamento confirmado: `Approved Date (ECO Automation) -> hq_eco_release_date (ECO CONTROL)`.
`Approved Date` corresponde a `HQ ECO RELEASE DATE` e NÃO corresponde a
`2ST APROV R&D FINISH (1)`. Esta integração não deve preencher
`second_aprov_rd_finish_1`. A regra do GAP 14D permanece inalterada.
O campo já existe no modelo e no schema geral da ECO; não requer migration.

### YES / NO

`auto_ecr` e `change_bom` são strings, não booleanos JSON:

```json
{
  "auto_ecr": "YES",
  "change_bom": "NO"
}
```

Esse fragmento ilustra os valores; uma chamada completa também exige `eco`.
`true` e `false` não substituem essas strings. A normalização remove espaços
externos, mas não converte caixa: envie `YES` ou `NO` em maiúsculas.

### Campos fora do contrato

Não enviar `Approved Date`, `Origin ECO`, `Suffix`, `Applied to Manaus?`,
`Prod Plan?` ou `Effective Date`, nem supostos equivalentes como `approved_date`,
`origin_eco`, `suffix`, `applied_to_manaus`, `prod_plan` e `effective_date`.

Também não enviar `group`, `group_name`, `owner`, `gap`, `gap_14d`, `au`,
`item`, `position`, `month` ou outros campos internos/derivados. Outros campos
da entidade ECO, como `agreement_*`, `second_aprov_rd_*`, `gap_14d_note` e
`set_eco`, tampouco fazem parte do schema.

A existência de uma coluna na entidade não a torna disponível nesta API.
Qualquer ampliação exige mudança formal do contrato.

## Valores omitidos, nulos e vazios

Para os campos opcionais, a integração aplica a seguinte regra conservadora:

| Valor recebido | Efeito |
|---|---|
| Campo omitido | Ignorado |
| `null` | Ignorado |
| `""` | Ignorado |
| `"   "` | Ignorado |
| Valor válido | Considerado para persistência |

Strings válidas têm espaços nas extremidades removidos; espaços internos são
preservados. Strings vazias são normalizadas para null antes da validação,
inclusive nos campos de data e YES/NO. `eco` é exceção: omitido, null ou vazio
é inválido e recebe 422.

O objetivo é impedir limpeza acidental de dados existentes. Na criação, valores
ignorados não preenchem os campos. Na atualização, preservam o valor armazenado.
Essa regra pertence ao endpoint da integração; não descreve a semântica do PATCH
genérico, que permite limpar campos. GROUP e OWNER continuam sendo aplicados
internamente mesmo quando nenhum campo opcional válido é recebido.

## Campos fixos GROUP e OWNER

> **Regra temporária atual da integração:** GROUP = BOM; OWNER = giseli.santos.

| Conceito | Nome usado pelo fluxo da API/permissões | Coluna interna | Valor |
|---|---|---|---|
| GROUP | `group` | `group_name` | `BOM` |
| OWNER | `owner` | `owner` | `giseli.santos` |

A automação **não envia esses campos**. `sync_automation` acrescenta os valores
internamente antes de chamar os fluxos normais de criação ou atualização.
Eles são aplicados também a ECOs existentes: valores diferentes são substituídos
e auditados; valores iguais não geram histórico adicional.

O GROUP explícito da integração prevalece sobre o mapeamento OWNER → GROUP.
As permissões normais continuam sendo verificadas, inclusive para esses campos.
A política está centralizada no ECO CONTROL e não deve ser duplicada na automação
ou no frontend. Quando mudar, alterar o backend e atualizar este documento.

## Matching e persistência

### Localização exata

`eco` identifica a sincronização. O repository executa igualdade equivalente a:

```sql
WHERE trim(ecos.eco) = :codigo_normalizado
```

O código recebido passa por `strip()`; a consulta aplica `trim()` ao código
armazenado, sem regravar globalmente os registros. Não usa contains, LIKE,
busca genérica ou listagem paginada. Não converte caixa nem colapsa espaços
internos; não conte com equivalência entre `ECO123` e `eco123`.

A consulta limita a leitura a dois registros para detectar ambiguidade e usa
`FOR UPDATE` para os registros encontrados. O limite não significa selecionar
um vencedor.

| Correspondências | Comportamento |
|---:|---|
| 0 | Cria uma ECO nova |
| 1 | Atualiza valores diferentes ou mantém a ECO |
| 2 ou mais | HTTP 409; não altera nenhuma e não cria uma terceira |

Não há escolha por primeira, última, menor ID ou mais recente. ECO inexistente
não retorna 404 neste fluxo: segue para criação, sujeita às permissões.

### Criação

O fluxo reutiliza `_create_eco` com os dados válidos disponíveis e as atribuições
fixas. Gera UUID e aplica as regras normais:

- `item`: maior ITEM atual mais um;
- `position`: maior posição atual mais um;
- `month`: abreviação definida pelo serviço para o mês do relógio do servidor;
- `au`: resultado do mapeamento OBU → AU, se houver OBU válido;
- `group_name = "BOM"` e `owner = "giseli.santos"`;
- `status = "WORKING"`, default atual do model;
- timestamps e demais defaults normais do model.

Os demais campos permanecem NULL, vazios ou com os defaults existentes. O backend
não inventa dados ausentes. Criar exige permissão geral de criação e permissões
de edição dos campos utilizados, conforme a seção de permissões.

### Atualização

`eco` não é alterado: funciona somente como identificador. Os opcionais válidos,
GROUP e OWNER passam pelo mesmo núcleo de atualização usado pelo PATCH.
Cada valor é comparado ao anterior; somente diferenças alteram o registro e
produzem histórico. O fluxo faz commit e realiza rollback em falhas na operação.

Por exemplo, enviar `title = "ABC"` e `auto_ecr = "YES"` para uma ECO que já
possui esses valores retorna `unchanged`, **desde que GROUP e OWNER também
estejam nos valores fixos** e nenhuma derivação de AU precise mudar.
Se apenas Title mudar, o resultado será `updated` com `changed_fields: ["title"]`.

### OBU → AU

```text
OBU válido recebido
→ consulta o mapeamento configurado no ECO CONTROL
→ determina AU internamente
```

A automação não envia `au`. O lookup usa igualdade do OBU normalizado. Se não
houver mapeamento, retorna None: na criação AU fica NULL e, na atualização com
OBU válido enviado, um AU anterior pode ser substituído por NULL. Se OBU for
omitido/nulo/vazio, essa derivação não é executada. Na atualização, uma mudança
efetiva de AU também aparece em `changed_fields` e no histórico.

## Respostas e idempotência

Todos os estados de sucesso usam **HTTP 200**, inclusive criação:

| `status` | Significado |
|---|---|
| `created` | Nova ECO criada |
| `updated` | Uma ECO existente teve pelo menos um valor alterado |
| `unchanged` | A ECO encontrada não precisava de alterações |

Schema real de saída:

```python
status: Literal["created", "updated", "unchanged"]
eco_id: str  # UUID serializado como string
eco: str
changed_fields: list[str]
```

`eco` na resposta é o valor persistido, que pode preservar espaços legados na
atualização; o identificador enviado não o reescreve.

### Nomes em changed_fields

- Na criação: lista as chaves válidas usadas como entrada da criação, incluindo
  `eco`, `group` e `owner`; não lista todos os defaults/gerados, como ITEM e AU.
- Na atualização: lista os campos efetivamente alterados com nomes públicos;
  GROUP aparece como **`group`**, OWNER como `owner`, e AU como `au`.
  A propriedade interna `group_name` é normalizada para `group` somente na
  resposta da integração, sem alterar model, permissões ou auditoria.
- Sem alterações: lista vazia. Não depender da ordem dos nomes.

Criação e atualização utilizam consistentemente `group` na resposta pública.
Isso não torna GROUP um campo aceito no payload; sua atribuição continua interna.

### Reexecução sequencial

Primeira chamada, supondo que ECO123 não exista:

```json
{
  "eco": "ECO123",
  "title": "Nova ECO"
}
```

Resposta:

```json
{
  "status": "created",
  "eco_id": "11111111-1111-4111-8111-111111111111",
  "eco": "ECO123",
  "changed_fields": ["eco", "title", "group", "owner"]
}
```

Segunda chamada idêntica:

```json
{
  "status": "unchanged",
  "eco_id": "11111111-1111-4111-8111-111111111111",
  "eco": "ECO123",
  "changed_fields": []
}
```

Terceira chamada:

```json
{
  "eco": "ECO123",
  "title": "Novo título"
}
```

Resposta:

```json
{
  "status": "updated",
  "eco_id": "11111111-1111-4111-8111-111111111111",
  "eco": "ECO123",
  "changed_fields": ["title"]
}
```

```text
1ª chamada → created
2ª chamada igual → unchanged
3ª chamada com alteração → updated
```

O UUID permanece o mesmo e valores iguais não acrescentam histórico. Isso
pressupõe ausência de alterações intermediárias nos campos/atribuições e no
mapeamento de AU usado pela requisição.

**Limite atual:** essa idempotência descreve reexecuções sequenciais quando há
uma única correspondência. `eco` não tem constraint unique e não existe chave
de idempotência nem bloqueio específico para um código ainda inexistente.
O código atual não garante exclusão de corrida entre criações simultâneas do
mesmo código. O cliente deve evitar envios paralelos para o mesmo ECO; se já
houver duplicidade, o servidor retorna 409.

## Status HTTP e erros

| HTTP | Situação atual | Ação esperada da automação |
|---:|---|---|
| 200 | `created`, `updated` ou `unchanged` | Registrar sucesso, UUID e estado |
| 401 | Login incorreto; JWT inválido/expirado; usuário do token inexistente/inativo | Revisar credenciais/estado da conta ou autenticar novamente conforme a causa |
| 403 | Bearer ausente/esquema incompatível; ou falta de permissão | Conferir header e depois permissões; não repetir indefinidamente |
| 409 | Código ECO ambíguo, com duas ou mais correspondências | Registrar conflito e solicitar correção; não escolher registro |
| 422 | Payload inválido, campo extra, ECO vazio, data ou YES/NO inválidos | Revisar os dados enviados |
| 500–599 | Erro interno ou indisponibilidade do servidor/infraestrutura | Registrar falha e aplicar política de timeout/retry do cliente |

O endpoint não implementa política própria de retries. Em falha de transporte,
o cliente pode não saber se o commit ocorreu; uma reexecução sequencial deve
seguir as condições e limites descritos na seção de idempotência.

Erros de negócio/autorização usam o formato FastAPI com `detail`, por exemplo:

```json
{
  "detail": "Código ECO ambíguo: mais de um registro encontrado"
}
```

No 422, `detail` normalmente é uma lista de erros de validação. Não tratar toda
resposta de erro como se `detail` fosse necessariamente string. O serviço não
define um corpo JSON específico para todo erro 500.

## Conta técnica da automação

### Perfil recomendado

Perfil mínimo para uma conta exclusiva da automação, capaz de criar e sincronizar
ECOs com qualquer payload aceito atualmente:

```yaml
Nome conceitual: ECO Automation
Role: analyst
active: true

can_create_eco: true
can_bulk_edit: false
can_view_history: false
```

Configurar `can_edit=true` somente para estes campos:

```text
eco
obu
change_reason
eco_type
az_eco_register_date
hq_eco_release_date
auto_ecr
change_bom
title
group
owner
```

### Permissões verificadas

| Configuração | Necessidade |
|---|---|
| `AnalystPermission.can_create_eco = True` | Criar quando o código ainda não existe |
| `eco.can_edit = True` | Necessário na criação: o código faz parte dos dados criados |
| `obu.can_edit`, `change_reason.can_edit`, `eco_type.can_edit` | Necessários quando esses opcionais válidos são utilizados |
| `az_eco_register_date.can_edit`, `auto_ecr.can_edit`, `change_bom.can_edit`, `title.can_edit` | Necessários quando esses opcionais válidos são utilizados |
| `hq_eco_release_date.can_edit = True` | Necessário quando Approved Date é enviado como data válida, mesmo se igual à armazenada |
| `group.can_edit = True`, `owner.can_edit = True` | Necessários em toda sincronização: o backend fixa `BOM` e `giseli.santos`, mesmo sem esses campos no payload |

Habilitar manualmente `hq_eco_release_date.can_edit = true` para a conta técnica
ECO Automation no banco/interface administrativa. O código não concede essa permissão.

As permissões são registros de `FieldPermission` por e-mail, campo e `can_edit`.
Use `group` como chave externa de permissão; o serviço também normaliza a chave
legada `group_name` para `group`.

A validação de edição ocorre **antes** da comparação dos valores: enviar um
campo válido já igual ao atual também exige sua permissão. GROUP e OWNER passam
por essa validação mesmo quando já estão corretos. Opcionais omitidos, null,
vazios ou somente espaços são ignorados e não exigem autorização por esse envio.

Para atualizar uma ECO existente, não é necessário `can_create_eco` nem editar
`eco`, pois o código é removido das alterações. Para criar, ambos são necessários.
AU é derivado após a validação de campos recebidos e não exige autorização
separada de edição de `au` nesse fluxo.

### can_view e privilégio mínimo

`can_view` **não é requisito técnico** para
`POST /api/v1/integrations/eco-automation`. A autorização da integração utiliza
`can_edit`. Uma conta exclusiva de automação não precisa de acesso visual.
`can_view` regula a visualização nos fluxos existentes e não substitui `can_edit`;
o resumo retornado pela integração não filtra seus campos por `can_view`.

A conta não necessita de admin, bulk edit, histórico visível, exclusão,
gerenciamento de usuários, gerenciamento de settings, importação Excel nem
permissões adicionais de edição. Manter `can_bulk_edit=false` e
`can_view_history=false`; essas permissões não são pré-requisitos da integração.
Administradores seguem a autorização normal existente, mas o perfil recomendado
é `analyst`, não `admin`.

### Limitação do modelo atual

As permissões por campo são compartilhadas pelo sistema. Portanto, uma conta
autorizada a editar esses campos pela integração também pode utilizá-los em
outras rotas autenticadas que reutilizem essas permissões, como o PATCH genérico.
Não existe atualmente uma permissão exclusiva `can_use_eco_automation`.

Isso é uma limitação conhecida e possível melhoria futura, não um bloqueador
da integração atual. Não interpretar a ausência de necessidade de outras funções
como garantia de que todas elas estejam bloqueadas para a conta autenticada.

### Backlog técnico

1. O login pode emitir token para usuário inativo (`active=false`), embora seu
   uso posterior seja rejeitado pela validação do usuário autenticado.
2. A redefinição de senha não revoga automaticamente JWTs existentes.
3. `eco` não possui constraint UNIQUE: idempotência sequencial não protege contra
   duas criações simultâneas do mesmo código.
4. Avaliar futuramente uma permissão/autenticação exclusiva para integrações.

Essas questões **não bloqueiam a primeira versão da ECO Automation**. São itens
de evolução técnica; este documento não implementa mudanças no sistema.

### Segurança da credencial

- Utilizar uma conta exclusiva da automação, com role `analyst`, não `admin`.
- Guardar a senha em secret ou variável de ambiente; nunca versioná-la.
- Nunca versionar tokens nem registrar Authorization em logs.
- Utilizar HTTPS fora de desenvolvimento.
- Manter o token somente em memória durante sua utilização e descartá-lo quando
  deixar de ser necessário.

Esta etapa é apenas documental: não criar usuário ou senha, não alterar
permissões reais e não gerar token. Nenhuma conta é criada ou configurada por
este documento.

## Auditoria

A integração reutiliza `EcoHistory`, sem mecanismo paralelo. Os eventos incluem
UUID/código da ECO, ITEM, chave/rótulo do campo, valor anterior, valor novo,
e-mail/nome do usuário autenticado, data/hora e ação.

- **Criação:** ação `created`, valor anterior NULL e valor novo para os campos
  efetivamente passados ao fluxo de criação, incluindo ECO, GROUP e OWNER.
  Não gera um evento por todo default/campo derivado: ITEM, position, month,
  status default e AU derivado não são auditados individualmente nessa criação.
- **Atualização:** ação `updated` somente para diferenças efetivas, incluindo
  GROUP, OWNER e AU quando alterado pela regra OBU → AU.
- **Valores iguais:** não acrescentam eventos; `unchanged` não gera histórico.

No histórico, a chave de GROUP continua sendo `group`, conforme a auditoria
existente. Datas são registradas em representação ISO.
As alterações de dados e o histórico usam a transação existente; falhas no fluxo
de criação/atualização são submetidas a rollback.

## Exemplos de chamadas

### Criação completa

Supondo ENMP900999 inexistente, usuário autorizado e token válido:

```http
POST /api/v1/integrations/eco-automation
Authorization: Bearer <access_token>
Content-Type: application/json
```

```json
{
  "eco": "ENMP900999",
  "obu": "NW1",
  "change_reason": "Performance Improvement",
  "eco_type": "REGULAR",
  "az_eco_register_date": "2026-10-27",
  "hq_eco_release_date": "2026-10-28",
  "auto_ecr": "YES",
  "change_bom": "YES",
  "title": "Alteração de componente"
}
```

Resposta ilustrativa, HTTP 200 (UUID fictício):

```json
{
  "status": "created",
  "eco_id": "22222222-2222-4222-8222-222222222222",
  "eco": "ENMP900999",
  "changed_fields": [
    "eco", "obu", "change_reason", "eco_type", "az_eco_register_date", "hq_eco_release_date",
    "auto_ecr", "change_bom", "title", "group", "owner"
  ]
}
```

### Payload mínimo com título

```json
{
  "eco": "ENMP900999",
  "title": "Alteração de componente"
}
```

Criação parcial é permitida: outros opcionais permanecem sem preenchimento/default,
além das atribuições e campos internos descritos acima. Se a ECO já existir,
somente Title e as atribuições fixas são considerados. O mínimo absoluto válido
é `{"eco":"ENMP900999"}`; ele também aplica GROUP e OWNER.

## Interface e segurança

### Comportamento complementar do frontend

A tela ECO Control consulta periodicamente a listagem a cada 3 segundos e pode
detectar IDs ainda desconhecidos na sessão, destacando-os por cerca de 4 segundos.
A carga inicial não recebe destaque. Filtros e paginação continuam valendo;
edição ativa pode suspender a atualização. Isso é comportamento da interface,
não uma garantia ou parte do contrato HTTP da integração.

### Boas práticas para o cliente

- Configurar URL e e-mail por variáveis de ambiente.
- Obter senha de secret ou variável de ambiente; nunca versioná-la.
- Nunca versionar tokens nem imprimir o header Authorization.
- Manter o token somente em memória e renovar o login quando necessário.
- Usar HTTPS nos ambientes reais.
- Conceder privilégios mínimos à conta técnica, sem torná-la administradora.
- Registrar resultados e erros sem expor credenciais.

Essas são recomendações de operação do cliente; o documento não cria secrets,
contas ou um mecanismo adicional de autenticação no servidor.

## Pendências funcionais

Ainda depende de definição/mapeamento: `Origin ECO`.
`Approved Date` já está mapeado para `hq_eco_release_date`, conforme o contrato acima.

Atualmente fora de escopo: `Suffix`, `Applied to Manaus?` e `Prod Plan?`.
`Effective Date` também permanece fora do contrato desta integração.
Nenhum desses campos deve ser enviado ou inferido a partir de nomes semelhantes
na entidade. Alterações futuras exigem confirmação funcional, implementação e
atualização deste documento.

## Fontes da implementação

Referências usadas para conferir o contrato:

- [Controller da integração](../server/app/controller/integration_controller.py)
- [Schemas da integração](../server/app/schemas/eco_automation.py)
- [EcoService](../server/app/services/eco_service.py): `sync_automation`,
  `_create_eco`, `_apply_update_transaction`, permissões e histórico.
- [EcoRepository](../server/app/repository/eco_repository.py): matching e sequências.
- [SettingsRepository](../server/app/repository/settings_repository.py): OBU → AU.
- [Model e defaults](../server/app/models/entities.py)
- [Controller de autenticação](../server/app/controller/auth_controller.py),
  [schema de login](../server/app/schemas/auth.py),
  [serviço de autenticação](../server/app/services/auth_service.py) e
  [JWT/Bearer](../server/app/utils/security.py)
- [Registro dos routers](../server/main.py)
- [Testes da integração](../server/tests/test_eco_automation.py): criação,
  atualização, duplicidade, normalização, permissões, auditoria, idempotência,
  rollback, rejeição de extras e atribuições fixas.
- [Componente ECO Control](../client/src/app/modules/eco-control/eco-control.component.ts):
  comportamento complementar de polling.

## Fluxograma final

```text
Automação
   |
   | POST /api/v1/auth/login (JSON: email, password)
   v
ECO CONTROL Auth
   |
   | access_token JWT
   v
POST /api/v1/integrations/eco-automation (Bearer)
   |
   | valida schema e procura código completo normalizado
   |
   +-- 0 ECOs --> permissões + campos fixos --> CREATE --> created
   |
   +-- 1 ECO ---> permissões + campos fixos --> dados mudaram?
   |                                             |
   |                                             +-- sim --> updated
   |                                             |
   |                                             +-- não --> unchanged
   |
   +-- 2+ ECOs -------------------------------------------> 409 Conflict
```
