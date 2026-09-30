# Documentação da API REST — ECO CONTROL

Este documento estabelece o contrato formal de integração entre o frontend (Angular) e o backend (FastAPI) do sistema **ECO CONTROL**.

---

## 1. Convenções Globais e URL Base

* **URL Base:** `http://localhost:8000/api/v1`
* **Formato Padrão:** `application/json` (com exceção do login, que recebe `application/x-www-form-urlencoded`).
* **Origem das Telas (Legado Base44):** As rotas atendem diretamente às visões migradas do protótipo no Base44.
* **Cabeçalho de Autenticação Obrigatório:**
  ```http
  Authorization: Bearer <access_token>
  ```

---

## 2. Endpoints de Autenticação (`/auth`)

### `POST /api/v1/auth/login`
Autentica o operador ou administrador e emite o token JWT de sessão.
* **Content-Type:** `application/x-www-form-urlencoded`
* **Parâmetros no Corpo:**
  * `username` *(string, obrigatório)*: Usuário ou e-mail.
  * `password` *(string, obrigatório)*: Senha.
* **Resposta de Sucesso (`HTTP 200 OK`):**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 28800,
    "user": {
      "id": 1,
      "username": "aluno",
      "role": "analyst"
    }
  }
  ```
* **Respostas de Erro:**
  * `HTTP 401 Unauthorized`: Credenciais incorretas ou conta inativa.

---

## 3. Gestão e Listagem de ECOs (`/ecos`)

### `GET /api/v1/ecos`
Alimenta a tabela principal de visualização de ECOs do frontend.
* **Parâmetros de Consulta (Query Params):**
  * `page` *(int, opcional, padrão: `1`)*: Página solicitada.
  * `limit` *(int, opcional, padrão: `20`)*: Quantidade de itens por página.
  * `status` *(string, opcional)*: `PROCESSADO_SUCESSO`, `PENDENTE_VALIDACAO_HUMANA` ou `REJEITADO_DADO_INVALIDO`.
  * `area` *(string, opcional)*: Área solicitante da alteração.
* **Resposta de Sucesso (`HTTP 200 OK`):**
  ```json
  {
    "total": 45,
    "page": 1,
    "limit": 20,
    "items": [
      {
        "id": 1,
        "codigo_eco": "ECO-00125",
        "titulo_alteracao": "Substituição de Painel Display",
        "area_solicitante": "Engenharia de Produto",
        "status_atual": "PROCESSADO_SUCESSO",
        "estimativa_orcamento": 1200.50,
        "data_implementacao_alvo": "2026-09-30"
      }
    ]
  }
  ```

### `GET /api/v1/ecos/{id}`
Carrega a ficha completa da ECO na tela de detalhes.
* **Parâmetro de Rota:** `id` *(int/string)*: Identificador interno ou Código da ECO.
* **Resposta de Sucesso (`HTTP 200 OK`):** Retorna os 15 campos da planilha de controle mestre:
  ```json
  {
    "id": 1,
    "codigo_eco": "ECO-00125",
    "titulo_alteracao": "Substituição de Painel Display",
    "area_solicitante": "Engenharia de Produto",
    "nome_engenheiro_responsavel": "André Lucas",
    "email_solicitante": "andre@lg.com",
    "data_recebimento": "2026-08-20T10:00:00",
    "nivel_prioridade": "ALTA",
    "status_atual": "PROCESSADO_SUCESSO",
    "justificativa_tecnica": "Ajuste de conformidade de engenharia",
    "codigo_item_afetado": "PN-7788.WZ",
    "categoria_mudanca": "DisplayMedia",
    "impacto_custos": "Médio",
    "estimativa_orcamento": 1200.50,
    "unidade_fabril": "Manaus",
    "data_implementacao_alvo": "2026-09-30"
  }
  ```
* **Respostas de Erro:**
  * `HTTP 404 Not Found`: Registro não localizado.

### `PUT /api/v1/ecos/{id}`
Atualiza campos operacionais permitidos durante a triagem ou validação humana.
* **Parâmetro de Rota:** `id` *(int/string)*: Identificador da ECO.
* **Corpo da Requisição (`application/json`):**
  ```json
  {
    "justificativa_tecnica": "Justificativa complementada pelo analista",
    "data_implementacao_alvo": "2026-10-15",
    "status_atual": "PROCESSADO_SUCESSO"
  }
  ```
* **Resposta de Sucesso (`HTTP 200 OK`):** Retorna o objeto atualizado com gravação automática no histórico de auditoria.
* **Respostas de Erro:**
  * `HTTP 403 Forbidden`: O perfil do usuário logado não possui permissão para editar os campos enviados.
  * `HTTP 422 Unprocessable Entity`: Erro de validação de tipos ou dados inválidos (ex.: orçamento negativo).

---

## 4. Dashboard e Indicadores (`/dashboard`)

### `GET /api/v1/dashboard/metrics`
Alimenta os cards numéricos e gráficos da interface.
* **Resposta de Sucesso (`HTTP 200 OK`):**
  ```json
  {
    "total_recebidas": 150,
    "processadas_sucesso": 120,
    "pendentes_validacao_humana": 20,
    "rejeitadas_dados_invalidos": 10,
    "taxa_automacao_percentual": 80.0
  }
  ```

---

## 5. Histórico e Trilha de Auditoria (`/ecos/{id}/history`)

### `GET /api/v1/ecos/{id}/history`
Retorna a linha do tempo de auditoria da ECO selecionada.
* **Resposta de Sucesso (`HTTP 200 OK`):**
  ```json
  [
    {
      "id": 1,
      "eco_id": 1,
      "usuario_responsavel": "joao.ausier",
      "data_modificacao": "2026-08-20T14:32:00",
      "campo_alterado": "status_atual",
      "valor_anterior": "PENDENTE_VALIDACAO_HUMANA",
      "valor_novo": "PROCESSADO_SUCESSO"
    }
  ]
  ```

---

## 6. Administração (`/admin`)

* **Acesso:** Restrito a usuários com perfil `admin`.
* `GET /api/v1/admin/users`: Lista analistas e administradores cadastrados.
* `POST /api/v1/admin/users`: Cadastro de novos usuários.
* `POST /api/v1/admin/reprocessar-lote`: Disparo manual para reprocessar pendências em lote.

---

## 7. Tabela de Códigos de Status HTTP Padronizados

| Código | Significado | Quando é retornado |
| :---: | :--- | :--- |
| **`200 OK`** | Sucesso | Requisição processada e dados retornados ou atualizados. |
| **`201 Created`** | Criado | Novo registro criado com sucesso. |
| **`400 Bad Request`** | Requisição Inválida | Sintaxe incorreta ou parâmetros inválidos. |
| **`401 Unauthorized`** | Não Autenticado | Token JWT ausente, inválido ou expirado. |
| **`403 Forbidden`** | Acesso Negado | Usuário autenticado, mas sem perfil para a ação/campo. |
| **`404 Not Found`** | Não Encontrado | Identificador de ECO ou rota inexistente. |
| **`422 Unprocessable`**| Erro de Validação | Falha no schema Pydantic (tipo incorreto ou valor proibido). |