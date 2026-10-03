# Autenticação, Autorização e Permissões — ECO CONTROL

Este documento descreve o mecanismo atual de autenticação e autorização do **ECO CONTROL**, incluindo o uso de JWT, os perfis de usuário, as permissões gerais dos analistas e as permissões específicas por campo.

A validação definitiva de acesso é realizada pelo backend FastAPI. O frontend utiliza as permissões para adaptar a interface, mas não substitui as validações realizadas pela API.

---

## 1. Visão Geral

O fluxo de segurança utiliza:

```text
E-mail + Senha
      ↓
FastAPI
      ↓
Validação da senha
      ↓
JWT
      ↓
Frontend Angular
      ↓
Authorization: Bearer <token>
      ↓
Rotas protegidas
```

Os perfis utilizados atualmente são:

```text
admin
analyst
```

---

## 2. Login

A autenticação é realizada através do endpoint:

```text
POST /api/v1/auth/login
```

O corpo da requisição utiliza JSON:

```json
{
  "email": "admin@eco.com",
  "password": "admin123"
}
```

O backend busca o usuário pelo e-mail e valida a senha armazenada em formato de hash.

Em caso de sucesso, retorna:

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

Em caso de credenciais inválidas:

```text
HTTP 401 Unauthorized
```

---

## 3. Senhas

As senhas não são armazenadas em texto puro.

O backend utiliza hash de senha com bcrypt.

O fluxo conceitual é:

```text
Senha informada
     ↓
bcrypt
     ↓
Comparação com hashed_password
     ↓
Login autorizado ou rejeitado
```

A tabela `users` armazena:

```text
hashed_password
```

e não a senha original.

---

## 4. Token JWT

Após o login, o backend gera um JWT assinado utilizando:

```text
HS256
```

O token contém informações como:

```text
sub   → UUID do usuário
email → e-mail
role  → perfil
exp   → expiração
```

O tempo de expiração é configurável pelo ambiente através de:

```text
access_token_minutes
```

Na configuração padrão de desenvolvimento:

```text
480 minutos
```

equivalentes a aproximadamente 8 horas.

---

## 5. Armazenamento no Frontend

O Angular atualmente armazena o token e os dados básicos do usuário no:

```text
localStorage
```

As chaves utilizadas são:

```text
eco_token
eco_user
```

Exemplo conceitual:

```typescript
localStorage.setItem(
  'eco_token',
  response.access_token
);

localStorage.setItem(
  'eco_user',
  JSON.stringify(response.user)
);
```

Ao efetuar logout, esses dados são removidos.

---

## 6. Envio do Token

O Angular possui um `HttpInterceptor` responsável por anexar automaticamente o token às requisições autenticadas.

Cabeçalho enviado:

```http
Authorization: Bearer <access_token>
```

Fluxo:

```text
Angular
   ↓
AuthInterceptor
   ↓
Authorization: Bearer TOKEN
   ↓
FastAPI
```

---

## 7. Validação no Backend

As rotas protegidas utilizam a dependência:

```text
current_user
```

O backend:

1. extrai o Bearer Token;
2. valida a assinatura JWT;
3. valida a expiração;
4. obtém o UUID do usuário através de `sub`;
5. consulta o usuário no banco;
6. verifica se a conta continua ativa.

Caso o token seja inválido ou o usuário esteja inativo:

```text
HTTP 401 Unauthorized
```

---

## 8. Tratamento de HTTP 401 no Frontend

Quando o `AuthInterceptor` recebe:

```text
401 Unauthorized
```

o frontend:

```text
remove token
     ↓
remove usuário local
     ↓
redireciona para /login
```

Essa lógica evita que uma sessão inválida continue sendo utilizada pela aplicação.

---

## 9. Guards do Angular

O frontend utiliza guards para controlar o acesso às rotas.

### `authGuard`

Verifica se existe token armazenado.

Quando não existe:

```text
/login
```

é utilizado como destino.

### `adminGuard`

Verifica se o usuário armazenado possui:

```text
role === "admin"
```

Se não possuir, o acesso à rota administrativa é bloqueado no frontend.

Esses guards representam uma proteção de interface.

A proteção definitiva continua sendo realizada pelo backend.

---

# 10. Perfis de Usuário

## 10.1. Administrador

O perfil:

```text
admin
```

possui acesso administrativo ao sistema.

Entre suas capacidades estão:

- criar ECOs;
- editar os campos permitidos pelo schema;
- utilizar importação em massa;
- visualizar o histórico;
- excluir uma ECO;
- excluir várias ECOs selecionadas;
- criar usuários;
- redefinir senhas;
- excluir usuários;
- configurar permissões;
- configurar OBU → AU;
- configurar OWNER → GROUP;
- gerenciar configurações administrativas.

Administradores não dependem das permissões individuais armazenadas em `analyst_permissions`.

---

## 10.2. Analista

O perfil:

```text
analyst
```

possui acesso operacional.

As permissões do analista são configuradas individualmente.

Existem dois níveis principais:

```text
Permissões gerais
+
Permissões por campo
```

---

# 11. Permissões Gerais do Analista

As permissões gerais são armazenadas na tabela:

```text
analyst_permissions
```

Campos:

```text
can_create_eco
can_bulk_edit
can_view_history
```

---

## 11.1. `can_create_eco`

Define se o analista pode criar novas ECOs.

```text
true
 ↓
pode criar

false
 ↓
criação bloqueada
```

A verificação é realizada pelo backend antes da persistência.

---

## 11.2. `can_bulk_edit`

Define se o analista pode utilizar operações de importação em massa.

Essa permissão é verificada nos endpoints:

```text
POST /api/v1/ecos/import/preview
POST /api/v1/ecos/import
```

Quando o usuário não possui a permissão:

```text
HTTP 403 Forbidden
```

é retornado.

---

## 11.3. `can_view_history`

Define se o analista pode visualizar e exportar o histórico.

Essa permissão afeta:

```text
GET /api/v1/history
GET /api/v1/history/export
```

Caso não possua acesso:

```text
HTTP 403 Forbidden
```

é retornado.

---

# 12. Permissões por Campo

As permissões específicas são armazenadas em:

```text
field_permissions
```

Cada configuração associa:

```text
usuário
+
campo
+
can_view
+
can_edit
```

---

## 12.1. `can_view`

Define se determinado campo pode ser visualizado pelo analista.

Exemplo:

```text
field_key = comments
can_view = false
```

Nesse caso, o backend pode remover esse campo da resposta antes de devolvê-la ao frontend.

Essa regra também é considerada no histórico para evitar exposição indireta de campos que o usuário não pode visualizar.

---

## 12.2. `can_edit`

Define se determinado campo pode ser modificado pelo analista.

Exemplo:

```text
field_key = owner
can_edit = true
```

permite editar:

```text
OWNER
```

Se o analista tentar alterar um campo sem autorização:

```text
HTTP 403 Forbidden
```

é retornado.

---

# 13. Validação das Alterações

Ao receber uma atualização de ECO:

```text
PATCH /api/v1/ecos/{eco_id}
```

o backend identifica somente os campos enviados.

Depois:

```text
Payload
   ↓
Campos enviados
   ↓
Usuário é admin?
 ┌───────┴────────┐
Sim              Não
 ↓                ↓
permite       consulta field_permissions
                  ↓
            can_edit = true?
             ┌────┴────┐
            Sim       Não
             ↓          ↓
          continua     403
```

Dessa forma, não basta ocultar um campo no frontend.

A autorização é validada novamente no backend.

---

# 14. Permissões de Visualização

Durante a serialização da ECO, o backend consulta as permissões do analista.

Campos configurados com:

```text
can_view = false
```

são removidos da resposta.

Fluxo:

```text
ECO no banco
     ↓
serialize()
     ↓
field_permissions
     ↓
remove campos proibidos
     ↓
resposta JSON
```

Administradores não passam por essa filtragem.

---

# 15. Histórico e Permissões

O histórico também respeita as permissões de visualização.

Caso um analista não possa visualizar determinado campo, o backend evita expor esse conteúdo através dos registros de auditoria.

Isso se aplica inclusive a snapshots gerados durante a criação da ECO.

---

# 16. Administração das Permissões

Administradores podem consultar todas as permissões através de:

```text
GET /api/v1/permissions
```

Também podem consultar um analista específico:

```text
GET /api/v1/permissions/{user_email}
```

e atualizar:

```text
PUT /api/v1/permissions/{user_email}
```

Exemplo:

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

---

# 17. Administração de Usuários

As seguintes operações são restritas a administradores:

```text
GET /api/v1/users
POST /api/v1/users
PATCH /api/v1/users/{user_id}/password
DELETE /api/v1/users/{user_id}
```

O backend utiliza a dependência:

```text
admin_user
```

Essa dependência executa:

```text
current_user
      ↓
role == admin?
 ┌────┴────┐
Sim       Não
 ↓         ↓
acesso     403
```

---

# 18. Usuários Inativos

A tabela `users` possui:

```text
active
```

Durante a autenticação das requisições, o backend verifica se o usuário continua ativo.

Se não estiver:

```text
HTTP 401 Unauthorized
```

é retornado.

Assim, um token ainda existente no frontend não garante acesso caso a conta tenha sido desativada.

---

# 19. Códigos de Segurança

| Código | Significado |
|---|---|
| `400 Bad Request` | Regra de segurança ou operação inválida |
| `401 Unauthorized` | Token inválido, expirado ou usuário inválido |
| `403 Forbidden` | Usuário autenticado sem permissão para a operação |
| `404 Not Found` | Usuário ou recurso não encontrado |
| `422 Unprocessable Entity` | Payload inválido |

---

# 20. Princípio de Autorização

A aplicação segue o princípio:

```text
Frontend
 ↓
melhora a experiência do usuário

Backend
 ↓
define a autorização real
```

Portanto, esconder botões ou campos no Angular não é considerado mecanismo suficiente de segurança.

Todas as operações críticas devem continuar sendo validadas no FastAPI.

---

# 21. Resumo

O modelo de autorização atual pode ser representado como:

```text
Usuário
  ↓
JWT
  ↓
role
  ↓
┌───────────────────────────────┐
│ admin                         │
│ acesso administrativo        │
└───────────────────────────────┘

ou

┌───────────────────────────────┐
│ analyst                       │
│                               │
│ analyst_permissions           │
│   can_create_eco              │
│   can_bulk_edit               │
│   can_view_history            │
│                               │
│ field_permissions             │
│   can_view                    │
│   can_edit                    │
└───────────────────────────────┘
```

A implementação do backend é a referência definitiva para as regras de autorização.